import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from src.contracts.context import RunContext, StageMetrics, StageOutput

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class Stage(ABC, Generic[TIn, TOut]):
    name: str

    @abstractmethod
    def run(self, ctx: RunContext, payload: TIn) -> StageOutput[TOut]:
        raise NotImplementedError

    def _metrics(self, t0: float, success: bool, **extra: Any) -> StageMetrics:
        return StageMetrics(
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            success=success,
            extra=extra,
        )
