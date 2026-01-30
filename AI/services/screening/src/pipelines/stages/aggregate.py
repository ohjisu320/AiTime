from dataclasses import dataclass

from src.contracts.context import FailureReason, QualityFlag, RunContext


@dataclass
class WindowStats:
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
    flags: list[QualityFlag] = []

    # Hard fail by timeout
    if seen_seconds >= ctx.config.max_total_time_sec:
        # TIMEOUT 시점에 기본적인 환경 지표에 따른 flag는 추가할 수 있으나,
        # 여기서는 대표적으로 NOISE/LOW_LIGHT를 예시로 넣음
        return (
            FailureReason.FAIL_TIMEOUT,
            [QualityFlag.NOISE_HIGH, QualityFlag.LOW_LIGHT],
            False,
        )

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

    # Pick 대표 failure_reason (UX 단순화)
    if QualityFlag.NOISE_HIGH in flags:
        return (FailureReason.FAIL_NOISE, flags, False)
    if QualityFlag.LOW_LIGHT in flags:
        return (FailureReason.FAIL_LOW_LIGHT, flags, False)
    if QualityFlag.TOO_FEW_FACES in flags or QualityFlag.TOO_MANY_FACES in flags:
        return (FailureReason.FAIL_FACE_COUNT, flags, False)
    return (FailureReason.FAIL_ROI_MISMATCH, flags, False)
