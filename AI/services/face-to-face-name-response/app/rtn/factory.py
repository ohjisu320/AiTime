from collections.abc import Callable

from app.rtn.pipeline.video_analyzer import VideoAnalyzer
from app.rtn.settings import RTNConfig
from app.rtn.types import FrameBGR


def build_analyzer(
    cfg: RTNConfig,
    *,
    debug_publish: Callable[[FrameBGR], None] | None = None,
    conf_th: float | None = None,
) -> VideoAnalyzer:
    th = float(conf_th) if conf_th is not None else float(cfg.face_det.min_conf)

    return VideoAnalyzer(
        vad_cfg=cfg.vad,
        face_cfg=cfg.face_det,
        face_mesh_cfg=cfg.face_mesh,
        crop_cfg=cfg.crop,
        track_cfg=cfg.track,
        role_cfg=cfg.role,
        roi_cfg=cfg.roi,
        gaze_cfg=cfg.gaze,
        contact_cfg=cfg.contact,
        analysis_cfg=cfg.analysis,
        conf_th=th,
        debug_publish=debug_publish,
    )
