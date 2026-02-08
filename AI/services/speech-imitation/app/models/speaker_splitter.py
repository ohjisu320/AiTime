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
    f0_mad_semitone: float | None = None
    squeal_ratio: float | None = None
    jitter_local: float | None = None
    shimmer_local: float | None = None
    hnr_db: float | None = None
    voiced_fraction: float | None = None


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

        # 1. First Pass: Extract Metrics
        # We need to collect all F0s to calculate dynamic threshold
        temp_results = []
        f0_collection = []

        for seg in segments:
            y = audio[seg.start_sample : seg.end_sample]
            metrics = self._analyze_prosody(y, sample_rate)

            mean_f0 = metrics.get("mean_f0")
            if mean_f0 is not None:
                f0_collection.append(mean_f0)

            temp_results.append((seg, metrics))

        # 2. Determine Threshold
        threshold = float(self._settings.PITCH_CHILD_HZ_THRESHOLD)
        if self._settings.ENABLE_DYNAMIC_THRESHOLD:
            dynamic_th = self._calculate_dynamic_threshold(f0_collection)
            if dynamic_th is not None:
                threshold = dynamic_th
                logger.info(
                    f"Dynamic Threshold Applied: {threshold:.1f} Hz (Static: {self._settings.PITCH_CHILD_HZ_THRESHOLD} Hz)"
                )
            else:
                logger.info(f"Dynamic Threshold Fallback: {threshold:.1f} Hz")

        # 3. Second Pass: Assign Labels
        for seg, metrics in temp_results:
            mean_f0 = metrics.get("mean_f0")
            mad = metrics.get("mad")
            squeal = metrics.get("squeal_ratio")
            hnr = metrics.get("hnr")

            if mean_f0 is None:
                out.append(
                    LabeledSegment(
                        segment=seg,
                        label=SpeakerLabel.UNKNOWN,
                        mean_f0_hz=None,
                        f0_mad_semitone=None,
                        squeal_ratio=None,
                        jitter_local=None,
                        shimmer_local=None,
                        hnr_db=None,
                        voiced_fraction=None,
                    )
                )
                logger.debug(
                    f"  seg [{seg.start_sec:.2f}-{seg.end_sec:.2f}s] F0=None -> UNKNOWN"
                )
                continue

            label = SpeakerLabel.CHILD if mean_f0 >= threshold else SpeakerLabel.ADULT
            out.append(
                LabeledSegment(
                    segment=seg,
                    label=label,
                    mean_f0_hz=float(mean_f0),
                    f0_mad_semitone=mad,
                    squeal_ratio=squeal,
                    jitter_local=metrics.get("jitter"),
                    shimmer_local=metrics.get("shimmer"),
                    hnr_db=metrics.get("hnr"),
                    voiced_fraction=metrics.get("voiced_fraction"),
                )
            )
            logger.debug(
                f"  seg [{seg.start_sec:.2f}-{seg.end_sec:.2f}s] "
                f"F0={mean_f0:.1f}Hz, MAD={mad if mad else 'N/A'}, "
                f"Squeal={squeal if squeal else 'N/A'}, "
                f"HNR={hnr if hnr else 'N/A'}",
                f" -> {label.value} (Th={threshold:.1f})",
            )
        return out

    def _calculate_dynamic_threshold(self, f0_values: list[float]) -> float | None:
        """
        Perform 1D K-Means clustering (K=2) on F0 values.
        Returns the decision boundary (mean of two centroids).
        Falls back to None if clustering is unreliable.
        """
        if len(f0_values) < int(self._settings.MIN_CLUSTERING_SAMPLES):
            return None

        data = np.array(f0_values, dtype=np.float32)

        # Init centroids (Min & Max to encourage split)
        c1 = np.min(data)
        c2 = np.max(data)

        # If range is too small, it's unimodal
        if (c2 - c1) < 1.0:  # Identical values
            return None

        # K-Means Loop (Max 10 iterations)
        for _ in range(10):
            # Assignment
            d1 = np.abs(data - c1)
            d2 = np.abs(data - c2)
            mask1 = d1 < d2  # Points belonging to C1

            # Update
            new_c1 = np.mean(data[mask1]) if np.any(mask1) else c1
            new_c2 = np.mean(data[~mask1]) if np.any(~mask1) else c2

            if np.abs(new_c1 - c1) < 0.1 and np.abs(new_c2 - c2) < 0.1:
                break

            c1, c2 = new_c1, new_c2

        # Unimodal Check (Distance in Semitones)
        # 12 * log2(C2/C1)
        semitone_diff = 12.0 * np.log2((max(c1, c2) + 1e-9) / (min(c1, c2) + 1e-9))

        if (
            semitone_diff < 3.0
        ):  # Less than 3 semitones diff -> Unlikely distinct speakers
            return None

        return (c1 + c2) / 2.0

    def _analyze_prosody(self, y: np.ndarray, sr: int) -> dict[str, float | None]:
        """
        Returns:
            { "mean_f0": ..., ... }
        """
        y = np.asarray(y, dtype=np.float32).reshape(-1)
        if len(y) < int(0.10 * sr):
            return {}

        try:
            import parselmouth

            sound = parselmouth.Sound(y, sampling_frequency=sr)

            fmin = float(self._settings.PITCH_FMIN)
            fmax = float(self._settings.PITCH_FMAX)

            # 1. Pitch & Voiced Fraction
            pitch = sound.to_pitch(pitch_floor=fmin, pitch_ceiling=fmax)
            pitch_values = pitch.selected_array["frequency"]
            voiced_mask = pitch_values > 0
            voiced_f0 = pitch_values[voiced_mask]

            total_frames = len(pitch_values)
            voiced_frames = len(voiced_f0)

            if voiced_frames == 0:
                return {}

            mean_f0 = float(np.mean(voiced_f0))
            voiced_fraction = (
                float(voiced_frames / total_frames) if total_frames > 0 else 0.0
            )

            # 2. Squeal Ratio
            squeal_thresh = float(self._settings.PITCH_SQUEAL_HZ_THRESHOLD)
            squeal_count = np.sum(voiced_f0 > squeal_thresh)
            squeal_ratio = float(squeal_count / voiced_frames)

            # 3. MAD (Semitone)
            st = 12.0 * np.log2(voiced_f0 + 1e-9)
            median_st = np.median(st)
            mad = float(np.mean(np.abs(st - median_st)))

            # 4. Jitter & Shimmer (PointProcess)
            # point_process = sound.to_point_process(pitch) -> doesn't exist in python parselmouth wrapper directly
            # Use praat.call
            point_process = parselmouth.praat.call([sound, pitch], "To PointProcess (cc)")

            # num_periods check? Parselmouth/Praat handles it
            # (returns nan or -1/undefined)
            # local jitter
            # (shortest=0.0001s, longest=0.02s, max_period_factor=1.3) default
            jitter = point_process.get_jitter_local(0.0001, 0.02, 1.3)

            # local shimmer
            shimmer = point_process.get_shimmer_local(0.0001, 0.02, 1.3, 1.6)

            # 5. HNR (Harmonicity)
            # to_harmonicity (
            #   time_step=0.01,
            #   min_pitch=75.0,
            #   silence_threshold=0.1,
            #   periods_per_window=1.0
            # )
            harmonicity = sound.to_harmonicity(min_pitch=fmin)
            # Get mean HNR of voiced frames only? Or global?
            # Usually we want HNR in speech regions.
            hnr_values = harmonicity.values
            # Filter -200 (silence/undefined)
            valid_hnr = hnr_values[hnr_values > -200]
            hnr_mean = float(np.mean(valid_hnr)) if len(valid_hnr) > 0 else None

            return {
                "mean_f0": mean_f0,
                "mad": mad,
                "squeal_ratio": squeal_ratio,
                "voiced_fraction": voiced_fraction,
                "jitter": float(jitter) if not np.isnan(jitter) else None,
                "shimmer": float(shimmer) if not np.isnan(shimmer) else None,
                "hnr": hnr_mean,
            }

        except Exception as e:
            logger.warning(f"Parselmouth analysis failed: {e}. Fallback to autocorr.")
            f0_fallback = _autocorr_pitch(
                y,
                sr,
                fmin=float(self._settings.PITCH_FMIN),
                fmax=float(self._settings.PITCH_FMAX),
            )
            return {"mean_f0": f0_fallback} if f0_fallback else {}


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
