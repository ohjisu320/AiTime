"""
VAD (Voice Activity Detection) 래퍼

우선 Silero VAD를 사용하고, 로딩/실행이 불가능한 환경에서는
간단한 에너지 기반 VAD로 fallback 합니다.

Reference:
    - Silero VAD: https://github.com/snakers4/silero-vad
"""

import logging
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
    VAD (Silero 우선, 실패 시 에너지 기반 fallback)
    """

    _get_speech_timestamps: Any = None
    _utils: Any = None

    def __init__(self) -> None:
        self._settings = get_settings()
        self._use_fallback = False

    def ensure_loaded(self) -> None:
        """Silero 로드 시도. 실패하면 fallback."""
        if self._model_loaded:
            return
        try:
            super().ensure_loaded()
        except Exception as e:
            logger.warning(f"Silero VAD 로드 실패 → fallback VAD 사용: {e}")
            self._use_fallback = True
            self._model_loaded = True  # fallback도 로드 완료로 취급

    def _load_model(self) -> None:
        import torch  # type: ignore

        logger.info("Silero VAD 모델 로딩...")
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
            trust_repo=True,
        )
        self._model = model
        self._utils = utils
        (
            self._get_speech_timestamps,
            _,  # save_audio
            _,  # read_audio
            _,  # VADIterator
            _,  # collect_chunks
        ) = utils
        logger.info("Silero VAD 모델 로드 완료")

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

        if not self._use_fallback and self._get_speech_timestamps is not None:
            return self._detect_silero(audio, sr)

        return self._detect_energy(audio, sr)

    def _detect_silero(self, audio: np.ndarray, sr: int) -> list[SpeechSegment]:
        import torch  # type: ignore

        # Silero는 float tensor 기대
        audio_t = torch.from_numpy(audio)

        speech_timestamps = self._get_speech_timestamps(
            audio_t,
            self._model,
            sampling_rate=sr,
            threshold=float(self._settings.VAD_THRESHOLD),
            min_speech_duration_ms=int(self._settings.VAD_MIN_SPEECH_DURATION_MS),
            min_silence_duration_ms=int(self._settings.VAD_MIN_SILENCE_DURATION_MS),
            window_size_samples=int(self._settings.VAD_WINDOW_SIZE_SAMPLES),
            speech_pad_ms=int(self._settings.VAD_SPEECH_PAD_MS),
            return_seconds=False,
        )

        segments: list[SpeechSegment] = []
        for ts in speech_timestamps:
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
