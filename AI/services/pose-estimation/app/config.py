# app/config.py
"""
환경 설정 관리 모듈.

모든 설정값은 환경 변수 또는 .env 파일에서 로드됩니다.
하드코딩된 매직 넘버를 제거하고 중앙 집중식으로 관리합니다.
"""

from dataclasses import dataclass
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Literal


# =========================================================================
# 표정 분석 설정 (Emotion Analysis)
# =========================================================================
@dataclass(frozen=True)
class EmotionConfig:
    """
    표정 분석 설정.
    
    Attributes:
        enable: 표정 분석 활성화 여부
        skip_frames: 프레임 샘플링 간격
        min_face_size: 최소 얼굴 크기 (픽셀)
        model_name: 표정 인식 모델 이름
        joy_threshold: ADOS B6 판정 임계값 (Happiness 비율 >= 이 값이면 B6=True)
        face_confidence_threshold: 얼굴 탐지 신뢰도 임계값
    """
    enable: bool = True
    skip_frames: int = 5
    min_face_size: int = 64
    model_name: str = "enet_b0_8_best_vgaf"
    joy_threshold: float = 0.1  # Happiness 비율 >= 10%이면 ADOS B6 = True
    face_confidence_threshold: float = 0.9


class Settings(BaseSettings):
    """
    애플리케이션 설정.
    
    환경 변수 우선순위:
    1. 시스템 환경 변수
    2. .env 파일
    3. 기본값
    """
    
    # =========================================================================
    # 서버 설정
    # =========================================================================
    APP_NAME: str = "ViTPose Motion Analyzer"
    APP_VERSION: str = "1.0.0"
    DEBUG_MODE: bool = Field(default=False, description="디버그 모드 활성화")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # =========================================================================
    # 모델 설정
    # =========================================================================
    PERSON_DETECTOR: str = Field(
        default="PekingU/rtdetr_r50vd_coco_o365",
        description="사람 감지 모델 (HuggingFace ID)"
    )
    POSE_MODEL: str = Field(
        default="usyd-community/vitpose-base-simple",
        description="자세 추정 모델 (HuggingFace ID)"
    )
    DEVICE: Literal["cuda", "cpu", "mps"] = Field(
        default="cuda",
        description="연산 장치"
    )
    
    # =========================================================================
    # 영상 처리 설정
    # =========================================================================
    TARGET_FPS: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="프레임 추출 목표 FPS"
    )
    MAX_VIDEO_FRAMES: int = Field(
        default=300,
        ge=10,
        le=1000,
        description="최대 추출 프레임 수"
    )
    MAX_VIDEO_DURATION_SEC: float = Field(
        default=30.0,
        description="최대 영상 길이 (초)"
    )
    SUPPORTED_VIDEO_FORMATS: list[str] = Field(
        default=[".mp4", ".webm", ".avi", ".mov"],
        description="지원 영상 포맷"
    )
    
    # =========================================================================
    # 자세 추정 설정
    # =========================================================================
    DEFAULT_THRESHOLD: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="기본 감지 신뢰도 임계값"
    )
    MIN_KEYPOINT_SCORE: float = Field(
        default=0.1,
        description="유효 키포인트 최소 점수"
    )
    MIN_VALID_KEYPOINTS: int = Field(
        default=8,
        description="유효 프레임 판정을 위한 최소 키포인트 수"
    )
    MIN_VALID_FRAME_RATIO: float = Field(
        default=0.1,
        description="경고를 발생시킬 최소 유효 프레임 비율"
    )
    
    # =========================================================================
    # 정규화 설정
    # =========================================================================
    NORMALIZATION_METHOD: Literal["torso", "bbox", "hip_center"] = Field(
        default="torso",
        description="기본 정규화 방식"
    )
    REFERENCE_HEIGHT: float = Field(
        default=1.0,
        description="정규화 기준 높이"
    )
    
    # =========================================================================
    # DTW 설정
    # =========================================================================
    DTW_DISTANCE_METRIC: Literal["euclidean", "cosine", "manhattan"] = Field(
        default="euclidean",
        description="DTW 거리 계산 방식"
    )
    DTW_WINDOW_RATIO: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sakoe-Chiba 윈도우 비율 (0이면 제약 없음)"
    )
    
    # =========================================================================
    # 유사도 계산 설정
    # =========================================================================
    SIMILARITY_UPPER_BODY_WEIGHT: float = Field(default=1, description="상체 가중치")
    SIMILARITY_LOWER_BODY_WEIGHT: float = Field(default=1, description="하체 가중치")
    SIMILARITY_HEAD_WEIGHT: float = Field(default=1, description="머리 가중치")
    
    # =========================================================================
    # 동작별 판정 임계값
    # =========================================================================
    THRESHOLD_CLAPPING: float = Field(default=0.6, description="손뼉치기 통과 기준")
    THRESHOLD_HURRAY: float = Field(default=0.6, description="만세 통과 기준")
    THRESHOLD_WALKING_BACK: float = Field(default=0.6, description="뒷걸음질 통과 기준")
    THRESHOLD_JUMPING: float = Field(default=0.6, description="제자리 뛰기 통과 기준")
    THRESHOLD_KICKING: float = Field(default=0.6, description="공 차기 통과 기준")
    THRESHOLD_THROWING: float = Field(default=0.6, description="공 던지기 통과 기준")
    
    # =========================================================================
    # RabbitMQ 설정 (추후 통합용)
    # =========================================================================
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    TASK_QUEUE: str = "analysis.req.task1"
    RESULT_QUEUE: str = "analysis.resp"
    
    # =========================================================================
    # Validators
    # =========================================================================
    @field_validator("DEVICE", mode="before")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """
        디바이스 유효성 검사.
        
        Args:
            v: 입력된 디바이스 값
            
        Returns:
            검증된 디바이스 값
        """
        import torch
        if v == "cuda" and not torch.cuda.is_available():
            print("!!!!!!!!!!!!!! CUDA 사용 불가, CPU로 폴백")
            return "cpu"
        if v == "mps" and not torch.backends.mps.is_available():
            print("!!!!!!!!!!!!!! MPS 사용 불가, CPU로 폴백")
            return "cpu"
        return v
    
    def get_action_threshold(self, action_type: str) -> float:
        """
        동작 유형별 판정 임계값 반환.
        
        Args:
            action_type: 동작 유형 문자열
            
        Returns:
            해당 동작의 통과 임계값
            
        Raises:
            ValueError: 알 수 없는 동작 유형
        """
        thresholds = {
            "clapping": self.THRESHOLD_CLAPPING,
            "hurray": self.THRESHOLD_HURRAY,
            "walking_back": self.THRESHOLD_WALKING_BACK,
            "jumping": self.THRESHOLD_JUMPING,
            "kicking": self.THRESHOLD_KICKING,
            "throwing": self.THRESHOLD_THROWING,
        }
        if action_type not in thresholds:
            raise ValueError(f"Unknown action type: {action_type}")
        return thresholds[action_type]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


class RabbitMQConfig:
    """
    RabbitMQ 연결 설정 클래스.
    
    settings에서 값을 가져오되, 생성자에서 오버라이드 가능.
    의존성 주입 패턴을 통해 테스트 용이성 확보.
    """
    
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        task_queue: str | None = None,
        result_queue: str | None = None,
    ):
        self.host = host or settings.RABBITMQ_HOST
        self.port = port or settings.RABBITMQ_PORT
        self.user = user or settings.RABBITMQ_USER
        self.password = password or settings.RABBITMQ_PASSWORD
        self.task_queue = task_queue or settings.TASK_QUEUE
        self.result_queue = result_queue or settings.RESULT_QUEUE
