from dataclasses import dataclass

from src.contracts.context import FailureReason, QualityFlag, RunContext


@dataclass
class WindowStats:
    # counts
    video_count: int
    audio_count: int

    # ratios in recent window
    noise_high_ratio: float
    low_light_ratio: float
    two_faces_ratio: float
    roi1_face_ratio: float
    roi2_face_ratio: float

    # scores (recent avg)
    avg_rms_dbfs: float
    avg_luma_mean: float


def decide(
    ctx: RunContext, stats: WindowStats, seen_seconds: float
) -> tuple[FailureReason | None, list[QualityFlag], bool]:
    """
    returns: (failure_reason, flags, passed)
    """
    if stats.video_count == 0 or stats.audio_count == 0:
        # Not enough data yet to decide
        return (None, [], False)

    flags: list[QualityFlag] = []

    # Collect flags based on ratios
    if stats.noise_high_ratio > ctx.config.audio_noise_high_ratio_max:
        flags.append(QualityFlag.NOISE_HIGH)
    if stats.low_light_ratio > ctx.config.video_low_light_ratio_max:
        flags.append(QualityFlag.LOW_LIGHT)
    if stats.two_faces_ratio < ctx.config.faces_two_faces_ratio_min:
        flags.append(QualityFlag.TOO_FEW_FACES)
    if stats.roi1_face_ratio < ctx.config.roi_face_ratio_min:
        flags.append(QualityFlag.ROI_FACE_MISSING_1)
    if stats.roi2_face_ratio < ctx.config.roi_face_ratio_min:
        flags.append(QualityFlag.ROI_FACE_MISSING_2)

    passed = (
        stats.noise_high_ratio <= ctx.config.audio_noise_high_ratio_max
        and stats.low_light_ratio <= ctx.config.video_low_light_ratio_max
        and stats.two_faces_ratio >= ctx.config.faces_two_faces_ratio_min
        and stats.roi1_face_ratio >= ctx.config.roi_face_ratio_min
        and stats.roi2_face_ratio >= ctx.config.roi_face_ratio_min
    )

    if passed:
        return (None, [], True)

    # Not passed. Pick failure_reason
    reason = None
    if QualityFlag.NOISE_HIGH in flags:
        reason = FailureReason.FAIL_NOISE
    elif QualityFlag.LOW_LIGHT in flags:
        reason = FailureReason.FAIL_LOW_LIGHT
    elif QualityFlag.TOO_FEW_FACES in flags or QualityFlag.TOO_MANY_FACES in flags:
        reason = FailureReason.FAIL_FACE_COUNT
    elif (
        QualityFlag.ROI_FACE_MISSING_1 in flags
        or QualityFlag.ROI_FACE_MISSING_2 in flags
    ):
        reason = FailureReason.FAIL_ROI_MISMATCH

    # If time up but no flags (should not happen usually), fallback to FAIL_TIMEOUT
    if reason is None and seen_seconds >= ctx.config.max_total_time_sec:
        reason = FailureReason.FAIL_TIMEOUT

    return (reason, flags, False)
