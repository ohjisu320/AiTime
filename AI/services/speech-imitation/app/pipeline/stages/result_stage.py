"""
ResultStage
- 컨텍스트 메타 정리
"""

import logging

from app.config import get_settings
from app.pipeline.context import PipelineContext, PipelineStatus
from app.pipeline.stages.base_stage import BaseStage

logger = logging.getLogger(__name__)


class ResultStage(BaseStage):
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "ResultStage"

    def validate(self, context: PipelineContext) -> str | None:
        return None

    def process(self, context: PipelineContext) -> None:
        context.extra["schema_version"] = self._settings.SCHEMA_VERSION
        # status set by orchestrator; ensure completed
        if context.status != PipelineStatus.FAILED:
            context.status = PipelineStatus.COMPLETED
        logger.info("결과 생성 완료")
