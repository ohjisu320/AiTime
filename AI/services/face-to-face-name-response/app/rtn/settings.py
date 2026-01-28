from dataclasses import dataclass, field
from typing import Any

from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    CropConfig,
    FaceDetConfig,
    FaceMeshConfig,
    GazeSmoothConfig,
    ROIConfig,
    RoleAssignConfig,
    TrackConfig,
    VADConfig,
)


@dataclass(frozen=True)
class EngineConfig:
    enable_mjpeg: bool = True
    jpeg_quality: int = 80


@dataclass(frozen=True)
class RTNConfig:
    """모든 하이퍼파라미터"""
    vad: VADConfig = field(default_factory=VADConfig)
    face_det: FaceDetConfig = field(default_factory=FaceDetConfig)
    face_mesh: FaceMeshConfig = field(default_factory=FaceMeshConfig)
    track: TrackConfig = field(default_factory=TrackConfig)
    role: RoleAssignConfig = field(default_factory=RoleAssignConfig)
    roi: ROIConfig = field(default_factory=ROIConfig)
    gaze: GazeSmoothConfig = field(default_factory=GazeSmoothConfig)
    contact: ContactConfig = field(default_factory=ContactConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    crop: CropConfig = field(default_factory=CropConfig)


@dataclass(frozen=True)
class RTNSettings:
    engine: EngineConfig = field(default_factory=EngineConfig)
    rtn: RTNConfig = field(default_factory=RTNConfig)


DEFAULT_SETTINGS = RTNSettings()


def legacy_build_engine_kwargs(
    settings: RTNSettings = DEFAULT_SETTINGS
) -> dict[str, Any]:
    c = settings.rtn
    e = settings.engine
    return {
        "enable_mjpeg": e.enable_mjpeg,
        "jpeg_quality": e.jpeg_quality,
        "window_s": c.analysis.window_s,
        "vad_merge_gap": c.vad.merge_gap_s,
        "vad_min_speech_ms": c.vad.min_speech_ms,
        "vad_min_silence_ms": c.vad.min_silence_ms,
        "min_contact_frames": c.contact.min_contact_frames,
        "warmup_s": c.role.warmup_s,
        "conf": c.face_det.min_conf,
        "debug": c.analysis.debug,
        "fps_override": c.analysis.fps_override,
    }


def legacy_build_analyzer_kwargs(
    settings: RTNSettings = DEFAULT_SETTINGS
) -> dict[str, Any]:
    c = settings.rtn
    return {
        "window_s": c.analysis.window_s,
        "vad_merge_gap": c.vad.merge_gap_s,
        "vad_min_speech_ms": c.vad.min_speech_ms,
        "vad_min_silence_ms": c.vad.min_silence_ms,
        "min_contact_frames": c.contact.min_contact_frames,
        "warmup_s": c.role.warmup_s,
        "conf": c.face_det.min_conf,
        "debug": c.analysis.debug,
        "fps_override": c.analysis.fps_override,
    }
