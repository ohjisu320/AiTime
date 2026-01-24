from collections.abc import Callable

from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    FaceDetConfig,
    GazeSmoothConfig,
    ROIConfig,
    RoleAssignConfig,
    TrackConfig,
    VADConfig,
)
from app.rtn.pipeline.video_analyzer import VideoAnalyzer
from app.rtn.types import FrameBGR


def build_analyzer(
    window_s: float = 5.0,
    vad_merge_gap: float = 0.3,
    vad_min_speech_ms: int = 250,
    vad_min_silence_ms: int = 250,
    min_contact_frames: int = 3,
    warmup_s: float = 1.0,
    conf: float = 0.6,
    debug: bool = False,
    fps_override: float | None = None,
    debug_publish: Callable[[FrameBGR], None] | None = None,
) -> VideoAnalyzer:
    vad_cfg = VADConfig(
        sr=16000,
        min_speech_ms=vad_min_speech_ms,
        min_silence_ms=vad_min_silence_ms,
        merge_gap_s=vad_merge_gap,
    )
    face_cfg = FaceDetConfig(min_conf=conf, model_selection=0)
    track_cfg = TrackConfig(max_age=8, min_hits=2, iou_threshold=0.3)
    role_cfg = RoleAssignConfig(warmup_s=warmup_s)
    roi_cfg = ROIConfig(mesh_dilate_px=14, bbox_fallback_dilate_px=28)
    gaze_cfg = GazeSmoothConfig()
    contact_cfg = ContactConfig(
        min_contact_frames=min_contact_frames, raycast_samples=11
    )
    analysis_cfg = AnalysisConfig(
        window_s=window_s, debug=debug, fps_override=fps_override
    )

    return VideoAnalyzer(
        vad_cfg=vad_cfg,
        face_cfg=face_cfg,
        track_cfg=track_cfg,
        role_cfg=role_cfg,
        roi_cfg=roi_cfg,
        gaze_cfg=gaze_cfg,
        contact_cfg=contact_cfg,
        analysis_cfg=analysis_cfg,
        conf_th=conf,
        debug_publish=debug_publish,
    )
