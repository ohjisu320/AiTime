import numpy as np
from src.contracts.context import (
    ROI,
    PreflightConfig,
    QualityFlag,
    RunContext,
    make_repro_keys,
)
from src.pipelines.stages.audio_quality import AudioQualityStage


def _make_ctx(thr_dbfs: float = -35.0) -> RunContext:
    cfg = PreflightConfig(
        schema_version="1.0",
        task_type="PREFLIGHT_SCREENING",
        window_sec=5.0,
        max_total_time_sec=20.0,
        sample_video_fps=10,
        target_faces=2,
        audio_noise_dbfs_threshold=thr_dbfs,
        audio_noise_high_ratio_max=0.2,
        video_luma_mean_threshold=60.0,
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


def test_audio_quiet_not_noisy() -> None:
    ctx = _make_ctx(thr_dbfs=-35.0)
    st = AudioQualityStage()

    # -60 dBFS 근처: 매우 조용
    pcm = (10 ** (-60 / 20)) * np.random.randn(16000).astype(np.float32)
    out = st.run(ctx, {"pcm": pcm, "sample_rate": 16000})

    assert out.payload["noisy"] is False
    assert QualityFlag.NOISE_HIGH not in out.quality_flags


def test_audio_loud_is_noisy() -> None:
    ctx = _make_ctx(thr_dbfs=-35.0)
    st = AudioQualityStage()

    # -20 dBFS 근처: 꽤 큼
    pcm = (10 ** (-20 / 20)) * np.random.randn(16000).astype(np.float32)
    out = st.run(ctx, {"pcm": pcm, "sample_rate": 16000})

    assert out.payload["noisy"] is True
    assert QualityFlag.NOISE_HIGH in out.quality_flags
