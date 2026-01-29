"""
파이프라인 오케스트레이터 (speech_imitation)

Default Stages:
    1) InputStage
    2) VadStage
    3) SpeakerStage
    4) TrialPlanStage
    5) ImitationJudgeStage
    6) ResultStage
"""

import logging
import uuid
from typing import Any

from app.config import get_settings
from app.pipeline.context import PipelineContext, PipelineStatus
from app.pipeline.stages import (
    ImitationJudgeStage,
    InputStage,
    ResultStage,
    SpeakerStage,
    TrialPlanStage,
    VadStage,
)
from app.pipeline.stages.base_stage import BaseStage
from app.utils.logger import setup_logging

logger = logging.getLogger(__name__)


class SpeechImitationPipelineOrchestrator:
    def __init__(self, stages: list[BaseStage] | None = None) -> None:
        self._settings = get_settings()
        setup_logging(self._settings.LOG_LEVEL)

        self._stages = stages or [
            InputStage(),
            VadStage(),
            SpeakerStage(),
            TrialPlanStage(),
            ImitationJudgeStage(),
            ResultStage(),
        ]

    def run(
        self, video_path: str, age_months: int, request_id: str | None = None
    ) -> dict[str, Any]:
        rid = request_id or f"req_{uuid.uuid4().hex[:12]}"
        context = PipelineContext(
            request_id=rid, video_path=video_path, age_months=int(age_months)
        )
        context.status = PipelineStatus.RUNNING

        for stage in self._stages:
            try:
                stage.run(context)
            except Exception as e:
                context.status = PipelineStatus.FAILED
                context.error = str(e)
                logger.exception(f"Stage 실패: {stage.name}: {e}")
                break

        # schema version
        context.extra["schema_version"] = self._settings.SCHEMA_VERSION

        if (
            context.status != PipelineStatus.FAILED
            and context.status != PipelineStatus.COMPLETED
        ):
            context.status = PipelineStatus.COMPLETED

        return context.to_result()
