from src.contracts.context import (
    ROI,
    PreflightConfig,
    QualityFlag,
    RunContext,
    make_repro_keys,
)
from src.pipelines.stages.roi_validate import ROIValidateStage


def _make_ctx(roi1: ROI, roi2: ROI) -> RunContext:
    cfg = PreflightConfig(
        schema_version="1.0",
        task_type="PREFLIGHT_SCREENING",
        window_sec=5.0,
        max_total_time_sec=20.0,
        sample_video_fps=10,
        target_faces=2,
        audio_noise_dbfs_threshold=-35.0,
        audio_noise_high_ratio_max=0.2,
        video_luma_mean_threshold=60.0,
        video_low_light_ratio_max=0.2,
        faces_two_faces_ratio_min=0.8,
        faces_min_face_area_ratio=0.01,
        roi_face_ratio_min=0.8,
        roi_1=roi1,
        roi_2=roi2,
        debug_enabled=False,
        debug_save_mismatch_only=True,
        debug_artifacts_dir="artifacts/preflight",
    )
    repro = make_repro_keys(run_id="test_run")
    return RunContext(repro=repro, config=cfg, roi_1=roi1, roi_2=roi2)


def test_roi_both_present() -> None:
    roi1 = ROI(x0=0.0, y0=0.0, x1=0.5, y1=1.0)
    roi2 = ROI(x0=0.5, y0=0.0, x1=1.0, y1=1.0)
    ctx = _make_ctx(roi1, roi2)

    st = ROIValidateStage()

    W, H = 640, 480
    # face1 left half, face2 right half
    bboxes = [(50, 50, 200, 250), (400, 60, 580, 260)]
    out = st.run(ctx, {"frame_wh": (W, H), "face_bboxes": bboxes})

    assert out.payload["roi1_has_face"] is True
    assert out.payload["roi2_has_face"] is True
    assert QualityFlag.ROI_FACE_MISSING_1 not in out.quality_flags
    assert QualityFlag.ROI_FACE_MISSING_2 not in out.quality_flags


def test_roi_one_missing() -> None:
    roi1 = ROI(x0=0.0, y0=0.0, x1=0.5, y1=1.0)
    roi2 = ROI(x0=0.5, y0=0.0, x1=1.0, y1=1.0)
    ctx = _make_ctx(roi1, roi2)

    st = ROIValidateStage()

    W, H = 640, 480
    # only left face
    bboxes = [(50, 50, 200, 250)]
    out = st.run(ctx, {"frame_wh": (W, H), "face_bboxes": bboxes})

    assert out.payload["roi1_has_face"] is True
    assert out.payload["roi2_has_face"] is False
    assert QualityFlag.ROI_FACE_MISSING_2 in out.quality_flags
