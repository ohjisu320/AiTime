import warnings
from collections.abc import Callable
from dataclasses import replace

from app.rtn.pipeline.video_analyzer import VideoAnalyzer
from app.rtn.settings import DEFAULT_SETTINGS, RTNConfig
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


def build_analyzer_legacy(
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
    """Deprecated kwargs-based builder.

    Kept temporarily to avoid breaking older call sites.
    Prefer:
        build_analyzer(DEFAULT_SETTINGS.rtn, ...)

    This wrapper creates a config derived from DEFAULT_SETTINGS so that
    behavior stays identical to previous defaults.
    """

    warnings.warn(
        "build_analyzer_legacy(...) is deprecated; \
            use build_analyzer(cfg, ...) instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    base = DEFAULT_SETTINGS.rtn

    cfg = replace(
        base,
        vad=replace(
            base.vad,
            merge_gap_s=vad_merge_gap,
            min_speech_ms=vad_min_speech_ms,
            min_silence_ms=vad_min_silence_ms,
        ),
        face_det=replace(base.face_det, min_conf=conf),
        role=replace(base.role, warmup_s=warmup_s),
        contact=replace(base.contact, min_contact_frames=min_contact_frames),
        analysis=replace(
            base.analysis,
            window_s=window_s,
            debug=debug,
            fps_override=fps_override,
        ),
    )

    return build_analyzer(cfg, debug_publish=debug_publish, conf_th=conf)


def build_analyzer_from_cfg(
    cfg: RTNConfig,
    *,
    debug_publish: Callable[[FrameBGR], None] | None = None,
    conf_th: float | None = None,
) -> VideoAnalyzer:
    """
    build_analyzer_from_cfg(...) is deprecated
    """

    warnings.warn(
        "build_analyzer_from_cfg(...) is deprecated; \
            use build_analyzer(cfg, ...) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return build_analyzer(cfg, debug_publish=debug_publish, conf_th=conf_th)
