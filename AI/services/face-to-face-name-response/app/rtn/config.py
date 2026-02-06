from dataclasses import dataclass


@dataclass(frozen=True)
class VADConfig:
    sr: int = 16000
    min_speech_ms: int = 250
    min_silence_ms: int = 250
    merge_gap_s: float = 0.3
    tmp_dirname: str = ".tmp_vad"


@dataclass(frozen=True)
class FaceDetConfig:
    min_conf: float = 0.6
    model_selection: int = 0  # MediaPipe FaceDetection: 0/1


@dataclass(frozen=True)
class TrackConfig:
    max_age: int = 8
    min_hits: int = 2
    iou_threshold: float = 0.3


@dataclass(frozen=True)
class RoleAssignConfig:
    warmup_s: float = 1.0  # role assignment warmup seconds


@dataclass(frozen=True)
class ROIConfig:
    mesh_dilate_px: int = 14
    bbox_fallback_dilate_px: int = 28


@dataclass(frozen=True)
class GazeSmoothConfig:
    alpha: float = 0.25
    max_jump: float = 0.12
    deadzone: float = 0.02
    gaze_scale: float = 1.6

    end_alpha: float = 0.30
    end_jump_px: float = 40.0


@dataclass(frozen=True)
class ContactConfig:
    min_contact_frames: int = 3
    raycast_samples: int = 11


@dataclass(frozen=True)
class AnalysisConfig:
    window_s: float = 5.0
    debug: bool = False
    fps_override: float | None = None


@dataclass(frozen=True)
class RabbitMQConfig:
    """RabbitMQ 연결 설정"""
    host: str = "rabbitmq"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    task_queue: str = "analysis.req.task3"
    result_queue: str = "analysis.resp"

@dataclass(frozen=True)
class EmotionConfig:
    enable: bool = True
    skip_frames: int = 5
    min_face_size: int = 64
    model_name: str = "enet_b0_8_best_vgaf"
    p95_latency_ms_max: int = 50
    
