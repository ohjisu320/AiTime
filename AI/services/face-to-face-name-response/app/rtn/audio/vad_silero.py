from dataclasses import dataclass
from typing import Any

from app.rtn.config import VADConfig


@dataclass
class _SileroState:
    loaded: bool = False
    model: Any | None = None
    get_speech_timestamps: Any | None = None


_STATE = _SileroState()


class SileroVAD:
    """
    torch.hub 기반 Silero VAD 래퍼.
    - 최초 1회 모델 다운로드 필요할 수 있음
    """

    def __init__(self, cfg: VADConfig) -> None:
        self.cfg = cfg
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        if _STATE.loaded:
            return

        import torch  # noqa: PLC0415

        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        (
            get_speech_timestamps,
            _save_audio,
            _read_audio,
            _VADIterator,
            _collect_chunks,
        ) = utils

        _STATE.model = model
        _STATE.get_speech_timestamps = get_speech_timestamps
        _STATE.loaded = True

    def segments_from_wav(self, wav_path: str) -> list[tuple[float, float]]:
        import soundfile as sf  # noqa: PLC0415
        import torch  # noqa: PLC0415

        audio, file_sr = sf.read(wav_path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if file_sr != self.cfg.sr:
            raise RuntimeError(
                f"WAV sample rate mismatch: expected {self.cfg.sr}, got {file_sr}"
            )

        if _STATE.model is None or _STATE.get_speech_timestamps is None:
            raise RuntimeError("SileroVAD not initialized properly.")

        wav = torch.from_numpy(audio).float()

        ts = _STATE.get_speech_timestamps(
            wav,
            _STATE.model,
            sampling_rate=self.cfg.sr,
            min_speech_duration_ms=self.cfg.min_speech_ms,
            min_silence_duration_ms=self.cfg.min_silence_ms,
            return_seconds=False,
        )

        segs = [(t["start"] / self.cfg.sr, t["end"] / self.cfg.sr) for t in ts]
        return [(float(s), float(e)) for s, e in segs]
