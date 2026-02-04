"""
파이프라인 Stage 베이스 클래스

- validate(): 실행 전 입력 검증
- process(): Stage의 실제 작업
- run(): 공통 로깅/타이밍/에러 처리 (Template Method)
"""

import logging
import time
from abc import ABC, abstractmethod

from app.pipeline.context import PipelineContext, PipelineStatus

logger = logging.getLogger(__name__)


class BaseStage(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def process(self, context: PipelineContext) -> None: ...

    def validate(self, context: PipelineContext) -> str | None:
        return None

    def run(self, context: PipelineContext) -> PipelineContext:
        err = self.validate(context)
        if err:
            logger.error(f"✖️ {self.name} 검증 실패: {err}")
            context.status = PipelineStatus.FAILED
            context.error = err
            raise ValueError(err)

        logger.info(f"🩷 {self.name} 시작")
        t0 = time.perf_counter()
        try:
            self.process(context)
        except Exception as e:
            elapsed = time.perf_counter() - t0
            context.processing_times[self.name] = float(elapsed)
            context.status = PipelineStatus.FAILED
            context.error = str(e)
            logger.exception(f"✖️ {self.name} 실패 ({elapsed:.2f}s): {e}")
            raise
        else:
            elapsed = time.perf_counter() - t0
            context.processing_times[self.name] = float(elapsed)
            logger.info(f"✅ {self.name} 완료 ({elapsed:.2f}s)")
        return context
