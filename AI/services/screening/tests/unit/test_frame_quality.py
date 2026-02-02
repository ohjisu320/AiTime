import numpy as np
from src.contracts.context import (
    ROI,
    PreflightConfig,
    QualityFlag,
    RunContext,
    make_repro_keys,
)
from src.pipelines.stages.frame_quality import FrameQualityStage


def _make_ctx(luma_thr: float = 60.0) -> RunContext:
    cfg = PreflightConfig(
        schema_version="1.0",
        task_type="PREFLIGHT_SCREENING",
        window_sec=5.0,
        max_total_time_sec=20.0,
        sample_video_fps=10,
        target_faces=2,
        audio_noise_dbfs_threshold=-35.0,
        audio_noise_high_ratio_max=0.2,
        video_luma_mean_threshold=luma_thr,
        video_low_light_ratio_max=0.2,
        faces_two_faces_ratio_min=0.8,
        faces_min_face_area_ratio=0.01,
        roi_face_ratio_min=0.8,
        roi_1=ROI(x0=0.05, y0=0.20, x1=0.45, y1=0.90),
        roi_2=ROI(x0=0.55, y0=0.20, x1=0.95, y1=0.90),
        debug_enabled=False,
        debug_save_mismatch_only=True,
        debug_artifacts_dir="artifacts/preflight",
    )
    repro = make_repro_keys(run_id="test_run")
    return RunContext(repro=repro, config=cfg, roi_1=cfg.roi_1, roi_2=cfg.roi_2)


def _solid_bgr(val: int, h: int = 240, w: int = 320) -> np.ndarray:
    img = np.full((h, w, 3), val, dtype=np.uint8)
    return img


def test_frame_dark_low_light() -> None:
    ctx = _make_ctx(luma_thr=60.0)
    st = FrameQualityStage()

    frame = _solid_bgr(20)
    out = st.run(ctx, {"frame_bgr": frame})

    assert out.payload["low_light"] is True
    assert QualityFlag.LOW_LIGHT in out.quality_flags
    assert out.payload["luma_mean"] < 60.0


def test_frame_bright_not_low_light() -> None:
    ctx = _make_ctx(luma_thr=60.0)
    st = FrameQualityStage()

    frame = _solid_bgr(200)
    out = st.run(ctx, {"frame_bgr": frame})

    assert out.payload["low_light"] is False
    assert QualityFlag.LOW_LIGHT not in out.quality_flags
    assert out.payload["luma_mean"] >= 60.0
