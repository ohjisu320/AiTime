"""
간이 화자 분리 (엄마/아기)

- diarization(예: pyannote)을 쓰지 않고,
  VAD 세그먼트별 pitch(F0) 평균으로 성인/아동을 구분합니다.
- 성인 여성과 아동 경계가 겹칠 수 있으므로, "휴리스틱"으로 취급합니다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import numpy as np

from app.config import get_settings
from app.models.vad import SpeechSegment

logger = logging.getLogger(__name__)


class SpeakerLabel(str, Enum):
    ADULT = "adult"
    CHILD = "child"
    UNKNOWN = "unknown"


@dataclass
class LabeledSegment:
    segment: SpeechSegment
    label: SpeakerLabel
    mean_f0_hz: float | None = None


class SpeakerSplitter:
    def __init__(self) -> None:
        self._settings = get_settings()

    def label_segments(
        self,
        segments: list[SpeechSegment],
        audio: np.ndarray,
        sample_rate: int,
    ) -> list[LabeledSegment]:
        out: list[LabeledSegment] = []
        threshold = float(self._settings.PITCH_CHILD_HZ_THRESHOLD)
        for seg in segments:
            y = audio[seg.start_sample : seg.end_sample]
            f0 = self._mean_f0(y, sample_rate)
            if f0 is None:
                out.append(LabeledSegment(seg, SpeakerLabel.UNKNOWN, None))
                logger.debug(
                    f"  seg [{seg.start_sec:.2f}-{seg.end_sec:.2f}s] F0=None -> UNKNOWN"
                )
                continue
            label = SpeakerLabel.CHILD if f0 >= threshold else SpeakerLabel.ADULT
            out.append(LabeledSegment(seg, label, float(f0)))
            logger.debug(
                f"  seg [{seg.start_sec:.2f}-{seg.end_sec:.2f}s] "
                f"F0={f0:.1f}Hz -> {label.value}"
            )
        return out

    def _mean_f0(self, y: np.ndarray, sr: int) -> float | None:
        y = np.asarray(y, dtype=np.float32).reshape(-1)
        if len(y) < int(0.10 * sr):
            return None

        try:
            import librosa  # type: ignore

            f0, voiced_flag, _ = librosa.pyin(
                y.astype(float),
                fmin=float(self._settings.PITCH_FMIN),
                fmax=float(self._settings.PITCH_FMAX),
                sr=sr,
            )
            voiced_f0 = f0[voiced_flag]
            if voiced_f0 is None or len(voiced_f0) == 0:
                return None
            m = float(np.nanmean(voiced_f0))
            if np.isnan(m):
                return None
            return m
        except Exception:
            # fallback: autocorrelation
            return _autocorr_pitch(
                y,
                sr,
                fmin=float(self._settings.PITCH_FMIN),
                fmax=float(self._settings.PITCH_FMAX),
            )


def _autocorr_pitch(y: np.ndarray, sr: int, fmin: float, fmax: float) -> float | None:
    # simple autocorrelation pitch; robust enough for fallback
    y = y - np.mean(y)
    if np.allclose(y, 0):
        return None

    # Hanning
    y = y * np.hanning(len(y)).astype(np.float32)

    corr = np.correlate(y, y, mode="full")[len(y) - 1 :]
    corr[0] = 0.0

    # search lags
    lag_min = int(sr / max(1e-6, fmax))
    lag_max = int(sr / max(1e-6, fmin))
    lag_max = min(lag_max, len(corr) - 1)
    if lag_max <= lag_min:
        return None

    lag = int(np.argmax(corr[lag_min:lag_max]) + lag_min)
    if lag <= 0:
        return None
    f0 = sr / lag
    if f0 < fmin or f0 > fmax:
        return None
    return float(f0)
