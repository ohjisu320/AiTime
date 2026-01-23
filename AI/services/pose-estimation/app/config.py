# AI/services/pose-estimation/app/config.py
"""설정 관리"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """환경 변수 기반 설정"""
    
    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    TASK_QUEUE: str = "pose_task_queue"
    RESULT_QUEUE: str = "pose_result_queue"
    
    # Model
    PERSON_DETECTOR: str = "PekingU/rtdetr_r50vd_coco_o365"
    POSE_MODEL: str = "usyd-community/vitpose-base-simple"
    DEVICE: str = "cuda"
    
    # Processing
    DEFAULT_THRESHOLD: float = 0.3
    MAX_VIDEO_FRAMES: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # Debug
    DEBUG_MODE: bool = False # 추가

settings = Settings()