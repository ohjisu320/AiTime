"""
VAD (Voice Activity Detection) 래퍼

Silero VAD v4 ONNX 모델을 로컬에서 실행합니다.
외부 인터넷 연결(Torch Hub)이나 무거운 PyTorch 의존성을 제거하고,
ONNX Runtime과 Numpy만 사용하여 추론 속도를 최적화합니다.

Reference:
    - Silero VAD: https://github.com/snakers4/silero-vad
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.config import get_settings
from app.models.base import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class SpeechSegment:
    """음성 구간 정보"""

    start_sec: float
    end_sec: float
    start_sample: int
    end_sample: int
    confidence: float = 1.0

    @property
    def duration_sec(self) -> float:
        return float(self.end_sec - self.start_sec)

    def __repr__(self) -> str:
        return (
            f"SpeechSegment({self.start_sec:.2f}s~{self.end_sec:.2f}s, "
            f"dur={self.duration_sec:.2f}s)"
        )


class VoiceActivityDetector(BaseModel[Any]):
    """
    VAD (Silero ONNX 우선, 실패 시 에너지 기반 fallback)
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._use_fallback = False
        self._onnx_vad: OnnxSileroVAD | None = None
        self._model_path = os.path.join(
            os.path.dirname(__file__), "assets", "silero_vad.onnx"
        )

    def ensure_loaded(self) -> None:
        """ONNX 모델 로드 시도. 실패하면 fallback."""
        if self._model_loaded:
            return

        # Check if asset exists
        if not os.path.exists(self._model_path):
            logger.warning(
                f"Silero ONNX 모델 파일 없음: {self._model_path} -> fallback"
            )
            self._use_fallback = True
            self._model_loaded = True
            return

        try:
            self._load_model()
            self._model_loaded = True
        except Exception as e:
            logger.warning(f"Silero ONNX 로드 실패 → fallback VAD 사용: {e}")
            self._use_fallback = True
            self._model_loaded = True

    def _load_model(self) -> None:
        logger.info(f"Silero VAD ONNX 로딩... ({self._model_path})")
        self._onnx_vad = OnnxSileroVAD(self._model_path)
        logger.info("Silero VAD ONNX 로드 완료")

    def predict(
        self, audio: np.ndarray, sample_rate: int | None = None
    ) -> list[SpeechSegment]:
        return self.detect(audio, sample_rate=sample_rate)

    def detect(
        self, audio: np.ndarray, sample_rate: int | None = None
    ) -> list[SpeechSegment]:
        """
        음성 활동 구간 탐지
        """
        self.ensure_loaded()
        sr = int(sample_rate or self._settings.SAMPLE_RATE)
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim != 1:
            audio = audio.reshape(-1)

        if len(audio) == 0:
            return []

        if not self._use_fallback and self._onnx_vad is not None:
            return self._detect_silero_onnx(audio, sr)

        return self._detect_energy(audio, sr)

    def _detect_silero_onnx(self, audio: np.ndarray, sr: int) -> list[SpeechSegment]:
        if self._onnx_vad is None:
            return []

        timestamps = self._onnx_vad.get_speech_timestamps(
            audio,
            sr,
            threshold=float(self._settings.VAD_THRESHOLD),
            min_speech_duration_ms=int(self._settings.VAD_MIN_SPEECH_DURATION_MS),
            min_silence_duration_ms=int(self._settings.VAD_MIN_SILENCE_DURATION_MS),
            speech_pad_ms=int(self._settings.VAD_SPEECH_PAD_MS),
        )

        segments: list[SpeechSegment] = []
        for ts in timestamps:
            s = int(ts["start"])
            e = int(ts["end"])
            segments.append(
                SpeechSegment(
                    start_sec=s / sr,
                    end_sec=e / sr,
                    start_sample=s,
                    end_sample=e,
                    confidence=1.0,
                )
            )
        return segments

    def _detect_energy(self, audio: np.ndarray, sr: int) -> list[SpeechSegment]:
        """
        에너지 기반 fallback VAD
        - frame RMS로 thresholding
        - min_speech/min_silence(ms) 적용
        """
        hop = int(sr * 0.01)  # 10ms
        win = int(sr * 0.03)  # 30ms
        if win <= 0 or hop <= 0:
            return []

        # RMS
        rms = []
        for i in range(0, max(1, len(audio) - win + 1), hop):
            frame = audio[i : i + win]
            rms.append(float(np.sqrt(np.mean(frame * frame) + 1e-9)))
        rms = np.asarray(rms, dtype=np.float32)

        if len(rms) == 0:
            return []

        # adaptive threshold: median + k*mad
        med = float(np.median(rms))
        mad = float(np.median(np.abs(rms - med)) + 1e-9)
        thr = med + 3.0 * mad

        voiced = rms > thr

        min_speech = int(self._settings.VAD_MIN_SPEECH_DURATION_MS / 10)  # frames
        min_silence = int(self._settings.VAD_MIN_SILENCE_DURATION_MS / 10)

        segments: list[SpeechSegment] = []

        i = 0
        while i < len(voiced):
            if not voiced[i]:
                i += 1
                continue
            start_i = i
            # extend while voiced or short silence
            silence = 0
            i += 1
            while i < len(voiced):
                if voiced[i]:
                    silence = 0
                else:
                    silence += 1
                    if silence > min_silence:
                        break
                i += 1
            end_i = i - silence

            if (end_i - start_i) >= max(1, min_speech):
                start_sample = start_i * hop
                end_sample = min(len(audio), end_i * hop + win)
                segments.append(
                    SpeechSegment(
                        start_sec=start_sample / sr,
                        end_sec=end_sample / sr,
                        start_sample=start_sample,
                        end_sample=end_sample,
                        confidence=0.5,
                    )
                )

        return segments


class OnnxSileroVAD:
    def __init__(self, model_path: str) -> None:
        try:
            import onnxruntime as ort

            # Set session options for CPU optimization
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = 1
            sess_options.inter_op_num_threads = 1
            sess_options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            )

            self.session = ort.InferenceSession(
                model_path,
                providers=["CPUExecutionProvider"],
                sess_options=sess_options,
            )
        except ImportError as e:
            raise ImportError("onnxruntime is required for OnnxSileroVAD") from e

        self.reset_states()

    def reset_states(self) -> None:
        # Silero VAD v4 State: (2, 1, 64)
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)

    def __call__(
        self, x: np.ndarray, sr: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        # x: (B, T) -> Silero expects (B, T) float32
        if x.ndim == 1:
            x = x[np.newaxis, :]  # (1, T)

        # sr must be int64 for ONNX input
        sr_arr = np.array([sr], dtype=np.int64)

        ort_inputs = {
            "input": x,
            "sr": sr_arr,
            "h": self._h,
            "c": self._c,
        }

        # Run inference
        out, h_new, c_new = self.session.run(None, ort_inputs)

        # Update states
        self._h = h_new
        self._c = c_new

        return out

    def get_speech_timestamps(
        self,
        audio: np.ndarray,
        sr: int,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 100,
        speech_pad_ms: int = 30,
        window_size_samples: int = 512,
    ) -> list[dict]:
        """
        Numpy implementation of get_speech_timestamps
        """
        self.reset_states()

        # Audio normalization OK? Original util does /32768 if int.
        # Here we assume float32 [-1, 1].

        # Chunk audio
        # Silero works best with chunks of 512, 1024, 1536 samples (for 16k)
        # For 8k: 256, 512, 768
        # Standard: 512 samples at 16k

        # Make sure audio is multiple of window_size_samples
        if len(audio) % window_size_samples != 0:
            pad_len = window_size_samples - (len(audio) % window_size_samples)
            audio = np.pad(audio, (0, pad_len))

        # Split into chunks of window_size_samples
        # (N, window_size)
        chunks = audio.reshape(-1, window_size_samples)

        speech_probs = []
        for chunk in chunks:
            # inference
            out = self(chunk, sr)  # out shape (1, 1) probability
            speech_probs.append(float(out[0][0]))

        # Thresholding logic
        # Converted from utils_vad.py

        triggered = False
        speech_start = 0

        speeches = []

        temp_end = 0

        # to seconds
        min_speech_samples = sr * min_speech_duration_ms / 1000
        min_silence_samples = sr * min_silence_duration_ms / 1000
        speech_pad_samples = sr * speech_pad_ms / 1000

        for i, prob in enumerate(speech_probs):
            current_time = i * window_size_samples

            if (prob >= threshold) and temp_end:
                temp_end = 0

            if (prob >= threshold) and not triggered:
                triggered = True
                speech_start = current_time
                continue

            if (prob < threshold - 0.15) and triggered:  # Hysteresis
                if not temp_end:
                    temp_end = current_time

                # Check silence duration
                if (current_time - temp_end) < min_silence_samples:
                    continue
                else:
                    # End of speech
                    speech_end = temp_end
                    temp_end = 0
                    triggered = False

                    # Validate duration
                    if (speech_end - speech_start) > min_speech_samples:
                        speeches.append(
                            {
                                "start": int(max(0, speech_start - speech_pad_samples)),
                                "end": int(
                                    min(len(audio), speech_end + speech_pad_samples)
                                ),
                            }
                        )

        # Check last segment
        if triggered:
            speech_end = len(audio)
            if (speech_end - speech_start) > min_speech_samples:
                speeches.append(
                    {
                        "start": int(max(0, speech_start - speech_pad_samples)),
                        "end": int(min(len(audio), speech_end + speech_pad_samples)),
                    }
                )

        return speeches
