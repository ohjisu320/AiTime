from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


# =========================
# Repro Keys (Non-Negotiable)
# =========================
class ReproKeys(BaseModel):
    code_sha: str = Field(default="unknown", description="git commit sha")
    dataset_version: str = Field(
        default="n/a", description="not used for online preflight"
    )
    config_version: str = Field(
        default="unknown", description="hash/version of configs/preflight.yaml"
    )
    env_lock_hash: str = Field(
        default="unknown", description="poetry.lock/uv.lock/conda-lock hash"
    )
    run_id: str = Field(description="unique run/session id")


class QualityFlag(str, Enum):
    NOISE_HIGH = "NOISE_HIGH"
    LOW_LIGHT = "LOW_LIGHT"
    TOO_MANY_FACES = "TOO_MANY_FACES"
    TOO_FEW_FACES = "TOO_FEW_FACES"
    ROI_FACE_MISSING_1 = "ROI_FACE_MISSING_1"
    ROI_FACE_MISSING_2 = "ROI_FACE_MISSING_2"
    FACE_TOO_SMALL = "FACE_TOO_SMALL"


class FailureReason(str, Enum):
    FAIL_NOISE = "FAIL_NOISE"
    FAIL_LOW_LIGHT = "FAIL_LOW_LIGHT"
    FAIL_FACE_COUNT = "FAIL_FACE_COUNT"
    FAIL_ROI_MISMATCH = "FAIL_ROI_MISMATCH"
    FAIL_TIMEOUT = "FAIL_TIMEOUT"


class ROI(BaseModel):
    """Normalized ROI rectangle (0..1)."""

    x0: float
    y0: float
    x1: float
    y1: float


class PreflightConfig(BaseModel):
    schema_version: str = "1.0"
    task_type: str = "PREFLIGHT_SCREENING"

    window_sec: float = 5.0
    max_total_time_sec: float = 20.0
    sample_video_fps: int = 10

    target_faces: int = 2

    audio_noise_dbfs_threshold: float = -35.0
    audio_noise_high_ratio_max: float = 0.2

    video_luma_mean_threshold: float = 60.0
    video_low_light_ratio_max: float = 0.2

    faces_two_faces_ratio_min: float = 0.8
    faces_min_face_area_ratio: float = 0.01

    roi_face_ratio_min: float = 0.8

    roi_1: ROI
    roi_2: ROI

    debug_enabled: bool = True
    debug_save_mismatch_only: bool = True
    debug_artifacts_dir: str = "artifacts/preflight"


class RunContext(BaseModel):
    """Pipeline Context (request/trace/config/timestamps)."""

    repro: ReproKeys
    trace_id: str = "trace_unknown"
    span_id: str = "span_root"
    parent_span_id: str | None = None
    idempotency_key: str | None = None
    attempt: int = 1

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_info: dict[str, Any] = Field(default_factory=dict)

    config: PreflightConfig
    roi_1: ROI
    roi_2: ROI


# =========================
# Stage Contract (Standard)
# =========================
TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class StageInput(BaseModel, Generic[TIn]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: RunContext
    payload: TIn


class StageMetrics(BaseModel):
    latency_ms: float
    success: bool
    # stage 핵심 metric은 stage_metrics.extra로 확장 가능
    extra: dict[str, Any] = Field(default_factory=dict)


class StageOutput(BaseModel, Generic[TOut]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    payload: TOut
    stage_metrics: StageMetrics
    quality_flags: list[QualityFlag] = Field(default_factory=list)
    failure_reason: str | None = None  # stage-level (optional)


def make_repro_keys(
    run_id: str,
    code_sha: str = "unknown",
    config_version: str = "unknown",
    env_lock_hash: str = "unknown",
    dataset_version: str = "n/a",
) -> ReproKeys:
    return ReproKeys(
        run_id=run_id,
        code_sha=code_sha,
        dataset_version=dataset_version,
        config_version=config_version,
        env_lock_hash=env_lock_hash,
    )
