from dataclasses import dataclass, field

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
    """All hyperparameters for the RTN analyzer pipeline."""

    # Use default_factory to avoid shared-instance pitfalls.
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
