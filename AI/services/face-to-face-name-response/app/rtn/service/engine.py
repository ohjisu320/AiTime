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
