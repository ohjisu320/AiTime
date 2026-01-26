from dataclasses import dataclass
from typing import Any

from app.rtn.config import VADConfig


@dataclass
class _SileroState:
    # 프로세스 단위 싱글톤 캐시:
    # - torch.hub.load(모델 로딩/다운로드)가 비싸므로 1회만 로드해 재사용
    # - 여러 SileroVAD 인스턴스가 생겨도 같은 모델을 공유
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
        # 이미 로드되어 있으면 재사용
        # TODO: 동시 호출 문제 있을 수 있음
        if _STATE.loaded:
            return

        import torch  # noqa: PLC0415

        # torch.hub.load는 로컬 캐시를 우선 사용, 없으면 다운로드
        # force_reload=False로 매번 재다운로드/재로딩 False
        # onnx로의 포맷 변경은 현재 필요 없음
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

        # soundfile은 numpy(float32)로 읽어서 torch tensor로 변환
        audio, file_sr = sf.read(wav_path, dtype="float32")

        # 입력을 mono로 강제
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # 샘플레이트 체크
        if file_sr != self.cfg.sr:
            raise RuntimeError(
                f"WAV sample rate mismatch: expected {self.cfg.sr}, got {file_sr}"
            )

        # 전역 캐시 상태 점검(초기화 누락 방지)
        if _STATE.model is None or _STATE.get_speech_timestamps is None:
            raise RuntimeError("SileroVAD not initialized properly.")

        wav = torch.from_numpy(audio).float()

        # 초 변환은 밑에서 한번에 처리
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
