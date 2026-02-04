from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from src.contracts.context import FailureReason, QualityFlag


class MsgType(str, Enum):
    PROGRESS = "progress"
    HINT = "hint"
    RESULT = "result"


class BaseMessage(BaseModel):
    type: MsgType
    run_id: str


class ProgressMessage(BaseMessage):
    type: MsgType = MsgType.PROGRESS
    progress: float = Field(ge=0.0, le=1.0)
    # 최근 윈도우 지표(비율/점수)
    ratios: dict[str, float] = Field(default_factory=dict)
    scores: dict[str, float] = Field(default_factory=dict)
    flags: list[QualityFlag] = Field(default_factory=list)


class HintMessage(BaseMessage):
    type: MsgType = MsgType.HINT
    hint: str
    flags: list[QualityFlag] = Field(default_factory=list)
    # API 명세 필드
    person_count: int = 0
    distance: int = 0


class ResultMessage(BaseMessage):
    type: MsgType = MsgType.RESULT
    passed: bool
    failure_reason: FailureReason | None = None
    flags: list[QualityFlag] = Field(default_factory=list)

    # 요약 지표
    ratios: dict[str, float] = Field(default_factory=dict)
    scores: dict[str, float] = Field(default_factory=dict)

    # API 명세 필드 (프레임 통계)
    total_frames: int = 0
    valid_frames: int = 0
    confidence: float = 0.0

    # 디버깅/분석용
    details: dict[str, Any] = Field(default_factory=dict)
