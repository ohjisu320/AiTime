# services/name_non_facing/app/config.py
"""
설정 관리 모듈

환경변수 또는 .env 파일에서 설정을 로드하며,
모든 하이퍼파라미터를 중앙 집중식으로 관리합니다.

Reference:
    - Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    - 12-Factor App Config: https://12factor.net/config
"""

from pathlib import Path
from enum import Enum
from functools import lru_cache # 캐싱
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# 프로젝트 기본 경로 (app/ 디렉토리)
BASE_DIR = Path(__file__).resolve().parent


class ReactionMode(str, Enum):
    """반응 판정 모드"""
    GAZE_ONLY = "gaze_only"
    VOICE_ONLY = "voice_only"
    OR = "or"
    AND = "and"
    WEIGHTED = "weighted"


class WhisperModelSize(str, Enum):
    """
    Whisper 모델 크기
    
    Reference: https://github.com/openai/whisper#available-models-and-languages
    
    | Model     | Parameters | VRAM   | Relative Speed |
    |-----------|------------|--------|----------------|
    | tiny      | 39 M       | ~1 GB  | ~32x           |
    | base      | 74 M       | ~1 GB  | ~16x           |
    | small     | 244 M      | ~2 GB  | ~6x            |
    | medium    | 769 M      | ~5 GB  | ~2x            |
    | large     | 1550 M     | ~10 GB | 1x             |
    | large-v3  | 1550 M     | ~10 GB | 1x             |
    | large-v3-turbo | 809 M | ~6 GB  | ~8x            |
    """
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V3 = "large-v3"
    LARGE_V3_TURBO = "large-v3-turbo"


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ===== 서버 설정 =====
    APP_NAME: str = "name_non_facing"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # ===== RabbitMQ 설정 =====
    # #TODO 은 백엔드 협의 후 변경 예정
    RABBITMQ_HOST: str = Field(
        default="localhost",
        description="RabbitMQ 호스트"
    )
    RABBITMQ_PORT: int = Field(
        default=5672,
        description="RabbitMQ 포트"
    )
    RABBITMQ_USER: str = Field(
        default="guest",
        description="RabbitMQ 사용자"
    )
    RABBITMQ_PASSWORD: str = Field(
        default="guest",
        description="RabbitMQ 비밀번호"
    )
    RABBITMQ_VHOST: str = Field(
        default="/",
        description="RabbitMQ Virtual Host"
    )
    RABBITMQ_HEARTBEAT: int = Field(
        default=600,
        description="RabbitMQ heartbeat interval (seconds)"
    )
    RABBITMQ_BLOCKED_CONNECTION_TIMEOUT: int = Field(
        default=300,
        description="RabbitMQ blocked connection timeout (seconds)"
    )
    RABBITMQ_INITIAL_RETRY_DELAY: int = Field(
        default=5,
        description="RabbitMQ 초기 재시도 지연 시간 (seconds)"
    )
    RABBITMQ_MAX_RETRIES: int = Field(
        default=5,
        description="RabbitMQ 최대 재시도 횟수"
    )
    INPUT_QUEUE: str = Field(
        default="analysis.req.task4",
        description="작업 요청 큐 (TODO: 백엔드 협의 후 확정)"
    )
    OUTPUT_QUEUE: str = Field(
        default="analysis.resp",
        description="결과 응답 큐 (TODO: 백엔드 협의 후 확정)"
    )
    
    # ===== 공통 오디오 설정 =====
    AUDIO_SAMPLE_RATE: int = Field(
        default=16000, # 1초 동안 소리를 16000번 쪼개서 샘플링(국룰)
        description="오디오 샘플레이트 (Whisper, VAD 표준)"
    )
    
    # ===== Silero VAD 설정 =====
    # Reference: https://github.com/snakers4/silero-vad
    VAD_THRESHOLD: float = Field(
        default=0.5, # 잡음이 심하면 0.6-7, 속삭이는 소리도 필요하면 0.3-4 정도로 조절
        ge=0.0,
        le=1.0,
        description="VAD 음성 감지 임계값 (0.0~1.0)"
    )
    VAD_MIN_SPEECH_DURATION_MS: int = Field(
        default=250, # 최소 .25초 이상 이어져야 발화로 간주
        description="최소 음성 구간 길이 (ms)"
    )
    VAD_MIN_SILENCE_DURATION_MS: int = Field(
        default=100,  # .1초 이상 무음이면 구간 분리. 짧은 명령 인식 상황이므로 짧게 설정
        description="음성 구간 내 허용되는 최소 무음 길이 (ms)"
    )
    VAD_WINDOW_SIZE_SAMPLES: int = Field(
        default=512, # 한 번에 처리하는 오디오 샘플 크기, # silero는 512, 1024, 1536 지원하는데, 512가 가장 빠름.
        description="VAD 윈도우 크기 (512 for 16kHz)"
    )
    VAD_SPEECH_PAD_MS: int = Field(
        default=30, # 감지된 목소리 앞 뒤 여유를 0.03초 주겠다.
        description="음성 구간 전후 패딩 (ms)"
    )
    
    # ===== pyannote-audio 설정 =====
    # Reference: https://github.com/pyannote/pyannote-audio
    DIARIZATION_USE_AUTH_TOKEN: Optional[str] = Field(
        default=None,
        description="HuggingFace 인증 토큰 (pyannote 모델 다운로드용)"
    )
    DIARIZATION_MIN_SPEAKERS: int = Field(
        default=1,
        description="최소 화자 수"
    )
    DIARIZATION_MAX_SPEAKERS: int = Field(
        default=2,
        description="최대 화자 수 (부모 + 아이)"
    )
    DIARIZATION_MIN_SEGMENT_DURATION: float = Field(
        default=0.5, # 최소 0.5초 이상이어야 화자 구간으로 인식
        description="최소 발화 구간 길이 (초)"
    )
    DIARIZATION_DEVICE: str = Field(
        default="cuda",
        description="화자 분리 실행 디바이스 (cuda/cpu)"
    )
    
    # ===== Whisper 설정 =====
    # Reference: https://github.com/openai/whisper
    WHISPER_MODEL_SIZE: WhisperModelSize = Field(
        default=WhisperModelSize.LARGE_V3_TURBO,
        description="Whisper 모델 크기"
    )
    WHISPER_LANGUAGE: str = Field(
        default="ko",
        description="음성 인식 언어"
    )
    WHISPER_DEVICE: str = Field(
        default="cpu",
        description="Whisper 실행 디바이스 (cuda/cpu). CUDA 12 cuBLAS 없으면 cpu 권장"
    )
    WHISPER_COMPUTE_TYPE: str = Field(
        default="float16",
        description="연산 타입 (float16/int8/float32)"
    )
    WHISPER_BEAM_SIZE: int = Field(
        default=5,
        description="빔 서치 크기"
    )
    WHISPER_WORD_TIMESTAMPS: bool = Field(
        default=True,
        description="단어별 타임스탬프 추출 여부"
    )
    
    # ===== 반응 판정 설정 =====
    REACTION_MODE: ReactionMode = Field(
        default=ReactionMode.OR,
        description="반응 판정 모드"
    )
    REACTION_TIMEOUT_SEC: float = Field(
        default=5.0,
        description="반응 대기 시간 (초)"
    )
    
    # ===== Vision 파라미터 =====
    # YOLO Head Detector
    YOLO_HEAD_MODEL: str = Field(
        default=str(BASE_DIR / "models" / "yolo_p2layer_jh.pt"),
        description=(
            "YOLO Head-specific 모델 경로\n"
            "  - yolo_p2layer_jh.pt: P2 layer 추가된 커스텀 모델 (뒤통수 등 가린 얼굴 영역에서도 정확도 향상)\n"
            "  - yolov8-head.pt: Fine-tuned head detection (Kaggle Human Head Dataset)\n"
            "  - yolov8n.pt: 일반 person detection (fallback)\n"
            "Note: Head-specific 모델 사용으로 person bbox 추정 로직 제거됨"
        )
    )
    YOLO_HEAD_CONFIDENCE: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="YOLO 탐지 최소 신뢰도 (Head-specific 모델용, 낮을수록 더 많이 탐지)"
    )
    ENABLE_VISUALIZATION_DEBUG: bool = Field(
        default=False,
        description="시각화 디버그 모드 활성화 (바운딩 박스, 시선 벡터 등 표시)"
    )
    VISUALIZATION_WARMUP_FRAMES: int = Field(
        default=45,
        ge=0,
        description="시각화 시작 전 워밍업 프레임 수 (tracking 안정화 대기)"
    )
    
    # 6DRepNet360 Head Pose
    SIXDREPNET_MODEL: str = Field(
        default="weights/6DRepNet360_300W_LP.pth",
        description="6DRepNet360 모델 경로"
    )
    SIXDREPNET_DEVICE: str = Field(
        default="cuda",
        description="6DRepNet360 실행 디바이스 (cuda/cpu)"
    )
    
    # 얼굴 탐지 (MediaPipe - deprecated)
    FACE_DETECTION_CONFIDENCE: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="[deprecated] 얼굴 탐지 최소 신뢰도"
    )
    FACE_MESH_CONFIDENCE: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="[deprecated] Face Mesh 최소 신뢰도"
    )
    
    # 부모/아이 구분
    FIRST_PERSON_FALLBACK: bool = Field(
        default=False,
        description="부모 미탐지 시 1인칭 모드 자동 활성화 (CLI --selfie 등으로 명시적 활성화 권장)"
    )
    
    # 시선 분석
    GAZE_ANGLE_THRESHOLD_DEG: float = Field(
        default=20.0,
        ge=0.0,
        le=180.0,
        description="시선 각도 임계값 (도) - 시선벡터와 위치벡터 사이 3D 공간 각도"
    )
    GAZE_STABILIZE_FRAMES: int = Field(
        default=3,
        ge=1,
        description="안정화 판정에 필요한 연속 프레임 수"
    )
    MIN_GAZE_DURATION_SEC: float = Field(
        default=0.5,
        description="최소 시선 유지 시간 (초)"
    )
    
    # Smoothing (떨림 방지)
    ENABLE_SMOOTHING: bool = Field(
        default=True,
        description="Head pose 및 Gaze 방향 smoothing 활성화"
    )
    SMOOTHING_ALPHA_POSE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Head pose smoothing 계수 (0: 부드럽게, 1: 원본 유지). EMA: new = alpha*curr + (1-alpha)*prev"
    )
    SMOOTHING_ALPHA_GAZE: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Gaze direction smoothing 계수 (0: 부드럽게, 1: 원본 유지)"
    )
    SMOOTHING_ALPHA_BBOX: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Bounding box smoothing 계수 (0: 부드럽게, 1: 원본 유지)"
    )
    
    # ===== Audio 파라미터 =====
    VOICE_REACTION_ENABLED: bool = Field(
        default=True,
        description="음성 반응 활성화 여부"
    )
    MIN_VOICE_DURATION_SEC: float = Field(
        default=0.3,
        description="최소 발화 시간 (초)"
    )
    VOICE_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7,
        description="음성 반응 신뢰도 임계값"
    )
    
    # ===== 비디오 처리 =====
    VIDEO_FPS_SAMPLE: int = Field(
        default=0,
        description="분석용 FPS 샘플링 (0: 원본 FPS 유지)"
    )


@lru_cache
def get_settings() -> Settings:
    """
    설정 싱글톤 인스턴스 반환
    
    lru_cache로 한 번만 로드되도록 보장
    """
    return Settings()
