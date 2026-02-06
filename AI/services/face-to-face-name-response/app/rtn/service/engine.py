from __future__ import annotations

from dataclasses import dataclass

from app.rtn.debug.broker import FrameBroker
from app.rtn.factory import build_analyzer
from app.rtn.pipeline.video_analyzer import VideoAnalyzer
from app.rtn.service.debug_stream import create_debug_router
from app.rtn.settings import DEFAULT_SETTINGS, RTNSettings


@dataclass
class RTNEngine:
    analyzer: VideoAnalyzer
    broker: FrameBroker


def build_engine(
    settings: RTNSettings = DEFAULT_SETTINGS,
) -> tuple[RTNEngine, object | None]:
    broker = FrameBroker(jpeg_quality=settings.engine.jpeg_quality)

    analyzer = build_analyzer(
        settings.rtn,
        debug_publish=(broker.publish if settings.engine.enable_mjpeg else None),
        conf_th=settings.rtn.face_det.min_conf,
    )

    router = create_debug_router(broker) if settings.engine.enable_mjpeg else None
    return RTNEngine(analyzer=analyzer, broker=broker), router


def build_engine_legacy(
    *,
    enable_mjpeg: bool = True,
    jpeg_quality: int = 80,
    # 아래는 (구) build_analyzer 파라미터 그대로 통과
    window_s: float = 5.0,
    vad_merge_gap: float = 0.3,
    vad_min_speech_ms: int = 250,
    vad_min_silence_ms: int = 250,
    min_contact_frames: int = 3,
    warmup_s: float = 1.0,
    conf: float = 0.6,
    debug: bool = False,  # 로컬 cv2.imshow
    fps_override: float | None = None,
    # Emotion
    emotion_enable: bool = True,
    emotion_skip_frames: int = 5,
    emotion_model: str = "enet_b0_8_best_vgaf",
) -> tuple[RTNEngine, object | None]:
    """Deprecated kwargs-based engine builder.

    analyzer = build_analyzer(
        window_s=window_s,
        vad_merge_gap=vad_merge_gap,
        vad_min_speech_ms=vad_min_speech_ms,
        vad_min_silence_ms=vad_min_silence_ms,
        min_contact_frames=min_contact_frames,
        warmup_s=warmup_s,
        conf=conf,
        debug=debug,
        fps_override=fps_override,
        # Emotion
        emotion_enable=emotion_enable,
        emotion_skip_frames=emotion_skip_frames,
        emotion_model=emotion_model,
        debug_publish=(broker.publish if enable_mjpeg else None),
    )

    base = DEFAULT_SETTINGS

    engine_cfg = replace(
        base.engine,
        enable_mjpeg=enable_mjpeg,
        jpeg_quality=jpeg_quality,
    )

    rtn_base = base.rtn
    rtn_cfg = replace(
        rtn_base,
        vad=replace(
            rtn_base.vad,
            merge_gap_s=vad_merge_gap,
            min_speech_ms=vad_min_speech_ms,
            min_silence_ms=vad_min_silence_ms,
        ),
        contact=replace(rtn_base.contact, min_contact_frames=min_contact_frames),
        role=replace(rtn_base.role, warmup_s=warmup_s),
        face_det=replace(rtn_base.face_det, min_conf=conf),
        analysis=replace(
            rtn_base.analysis,
            window_s=window_s,
            debug=debug,
            fps_override=fps_override,
        ),
    )

    settings = replace(base, engine=engine_cfg, rtn=rtn_cfg)
    return build_engine(settings)


def build_engine_from_settings(
    settings: RTNSettings = DEFAULT_SETTINGS,
) -> tuple[RTNEngine, object | None]:
    """
    build_engine_from_settings(...) is deprecated
    """

    warnings.warn(
        "build_engine_from_settings(...) is deprecated; \
            use build_engine(settings) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return build_engine(settings)
