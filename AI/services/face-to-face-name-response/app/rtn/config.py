from dataclasses import dataclass


@dataclass(frozen=True)
class VADConfig:
    sr: int = 16000
    min_speech_ms: int = 250
    min_silence_ms: int = 250
    merge_gap_s: float = 0.3
    tmp_dirname: str = ".tmp_vad"


@dataclass(frozen=True)
class YOLOConfig:
    model_path: str = "app/assets/models/yolov11n-face.onnx"
    input_size: int = 640
    conf_thres: float = 0.5
    iou_thres: float = 0.45


@dataclass(frozen=True)
class FaceDetConfig:
    min_conf: float = 0.6
    model_selection: int = 2  # 0: MediaPipe, 1: YOLOv11n-face, 2: OpenVINO
    yolo_cfg: YOLOConfig = YOLOConfig()


@dataclass(frozen=True)
class FaceMeshConfig:
    """MediaPipe FaceMesh 파라미터.

    TODO: 실제 연동
    """

    refine_landmarks: bool = True
    det_min_conf: float = 0.3
    trk_min_conf: float = 0.5
    trk_min_track: float = 0.5
    min_crop_size: int = 160
    upscale_to: int = 256


@dataclass(frozen=True)
class CropConfig:
    """crop_face_square 여유(margin) 휴리스틱."""

    parent_margin: float = 0.25
    child_margin: float = 0.40


@dataclass(frozen=True)
class TrackConfig:
    max_age: int = 30
    min_hits: int = 3
    iou_threshold: float = 0.3

    # ByteTrack parameters
    high_thresh: float = 0.6
    low_thresh: float = 0.1
    second_iou_thresh: float = 0.5


@dataclass(frozen=True)
class RoleAssignConfig:
    warmup_s: float = 1.0  # role assignment warmup seconds


@dataclass(frozen=True)
class ROIConfig:
    mesh_dilate_px: int = 14
    bbox_fallback_dilate_px: int = 28

    # FaceMesh 실패 시 bbox fallback ROI 근사(비율 휴리스틱)
    # - x: 좌우 15%~85%
    # - y: 위 18%~55%
    bbox_fallback_x1_ratio: float = 0.15
    bbox_fallback_x2_ratio: float = 0.85
    bbox_fallback_y1_ratio: float = 0.18
    bbox_fallback_y2_ratio: float = 0.55


@dataclass(frozen=True)
class GazeSmoothConfig:
    alpha: float = 0.5  # 0.25 -> 0.5: faster response (less lag)
    max_jump: float = 0.15  # 0.12 -> 0.15: allow slightly larger jumps
    deadzone: float = 0.02
    gaze_scale: float = 2.5  # 1.6 -> 2.5: longer gaze line
    gaze_y_offset: float = -0.03  # NEW: shift gaze slightly UP (negative = up)

    end_alpha: float = 0.45  # 0.30 -> 0.45: faster end point response
    end_jump_px: float = 50.0  # 40 -> 50: allow larger jumps

    # Kalman Filter Options
    filter_type: str = "kalman"  # "alpha" | "kalman"
    kf_process_noise: float = 0.01  # Q: 낮을수록 부드러움 (지연 증가)
    kf_measurement_noise: float = 0.1  # R: 높을수록 부드러움 (지연 증가)


@dataclass(frozen=True)
class ContactConfig:
    min_contact_frames: int = 1
    raycast_samples: int = 81


@dataclass(frozen=True)
class AnalysisConfig:
    window_s: float = 5.0
    debug: bool = False
    fps_override: float | None = None

    # fps sanity check / fallback
    fps_min_valid: float = 1e-3
    fallback_fps: float = 30.0


@dataclass(frozen=True)
class RabbitMQConfig:
    """RabbitMQ 연결 설정"""

    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    task_queue: str = "face_name_task_queue"
    result_queue: str = "face_name_result_queue"


@dataclass(frozen=True)
class EmotionConfig:
    enable: bool = True
    skip_frames: int = 5
    min_face_size: int = 64
    model_name: str = "enet_b0_8_best_vgaf"
    p95_latency_ms_max: int = 50
