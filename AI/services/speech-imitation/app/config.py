"""
설정 관리 모듈 (speech_imitation)

- 12~23개월 아기의 "발화 모방(speech imitation)" 판정 파이프라인을 위한
  모든 하이퍼파라미터를 중앙에서 관리합니다.
- .env / 환경변수 기반 구성 (Pydantic Settings)

Reference:
    - Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    - 12-Factor App Config: https://12factor.net/config
"""

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgeBand(str, Enum):
    """월령 밴드"""

    M12_17 = "M12_17"
    M18_23 = "M18_23"


class SimilarityMode(str, Enum):
    """오디오 유사도 계산 모드"""

    MFCC_DTW = "mfcc_dtw"


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== 서비스 기본 =====
    APP_NAME: str = "speech_imitation"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SCHEMA_VERSION: str = "1.0"

    # ===== RabbitMQ (옵션) =====
    # RABBITMQ_URL: str = Field(description="RabbitMQ 연결 URL")
    # INPUT_QUEUE: str = Field(description="입력 큐 이름")
    # OUTPUT_QUEUE: str = Field(description="출력 큐 이름")
    # MAX_RETRIES: int = 3

    RABBITMQ_URL: str = Field(
        default="amqp://guest:guest@rabbitmq:5672/", description="RabbitMQ 연결 URL"
    )
    INPUT_QUEUE: str = "analysis.req.task2"
    OUTPUT_QUEUE: str = "analysis.resp"
    MAX_RETRIES: int = 3

    # ===== 오디오 전처리 =====
    SAMPLE_RATE: int = 16000
    MONO: bool = True

    # ===== 과제(프로토콜) =====
    # trial당 3번 반복
    REPETITIONS_PER_TRIAL: int = 1

    # Protocol Timing (Fixed Slots)
    TRIAL_DURATION_SEC: float = 8.0
    STIMULUS_SEARCH_WINDOW_SEC: float = 3.0

    # 월령 밴드별 자극(엄마가 말하는 단어/구)
    STIMULI_M12_17: list[str] = Field(
        default_factory=lambda: ["아", "마", "바", "맘마", "까꿍"],
        description="12~17개월 자극 목록",
    )
    STIMULI_M18_23: list[str] = Field(
        default_factory=lambda: ["엄마", "우유", "자동차", "까까 주세요", "야호!"],
        description="18~23개월 자극 목록",
    )

    STIMULUS_SET_ID_M12_17: str = "VOCAL_IMIT_KR_M12_17_V1"
    STIMULUS_SET_ID_M18_23: str = "VOCAL_IMIT_KR_M18_23_V1"

    # ===== 자극/반응 타이밍 가정(휴리스틱) =====
    # 엄마 자극 발화로 간주할 최대 길이(초): 너무 긴 문장은 제외
    STIMULUS_MAX_SEC: float = 2.0
    STIMULUS_MIN_SEC: float = 0.15

    # 자극 종료 후 이 시간 안에 아기 발화가 나오면 "반응 후보"
    RESPONSE_TIMEOUT_SEC: float = 5.0

    # 아기 발화 길이 필터
    RESPONSE_MIN_SEC: float = 0.12
    RESPONSE_MAX_SEC: float = 4.0

    # ===== VAD (Silero) =====
    VAD_THRESHOLD: float = 0.3
    VAD_MIN_SPEECH_DURATION_MS: int = 50
    VAD_MIN_SILENCE_DURATION_MS: int = 10
    VAD_SPEECH_PAD_MS: int = 0
    VAD_WINDOW_SIZE_SAMPLES: int = 512

    # ===== 화자(엄마/아기) 간이 분리 =====
    # pitch(F0)가 이 값 이상이면 아기로 간주(여성/아동 경계)
    PITCH_CHILD_HZ_THRESHOLD: float = 200.0
    ENABLE_DYNAMIC_THRESHOLD: bool = True
    MIN_CLUSTERING_SAMPLES: int = 3

    # pitch 추정 파라미터
    PITCH_FMIN: float = 50.0
    PITCH_FMAX: float = 1000.0

    # ===== 유사도(MFCC+DTW) =====
    SIMILARITY_MODE: SimilarityMode = SimilarityMode.MFCC_DTW

    # MFCC 파라미터
    N_MFCC: int = 13
    N_MELS: int = 40
    WIN_LENGTH_MS: float = 25.0
    HOP_LENGTH_MS: float = 10.0

    # DTW
    DTW_RADIUS: int = 20  # 1이면 일반 DTW에 가깝고, >1이면 탐색 창 제한
    SIMILARITY_THRESHOLD: float = 0.29  # "비슷한 소리면 OK" 기준 (튜닝 대상)

    # ===== 운율 분석 (Prosody Analysis) =====
    PITCH_SQUEAL_HZ_THRESHOLD: float = 450.0  # Squeal(끼익) 판별 주파수
    PITCH_MAD_MONOTONE_THRESHOLD: float = 1.0  # 단조로움 기준 (semitone)
    PITCH_MAD_SONG_THRESHOLD: float = 2.0  # 과장된 억양 기준 (semitone)

    # ===== 일관성 체크 (Consistency Check) =====
    # 아기 발화로 판정된 구간들 중에서도,
    # 전체 평균과 너무 동떨어진(예: 1옥타브 이상) 건 제외
    CONSISTENCY_SEMITONE_THRESHOLD: float = 12.0

    # ===== 디버그 산출물(옵션) =====
    # 예: debug/speech_imitation_20260129_153000/
    DEBUG_OUT_DIR: str | None = "./debug_output"
    SAVE_WAV_CLIPS: bool = True


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤"""
    return Settings()
