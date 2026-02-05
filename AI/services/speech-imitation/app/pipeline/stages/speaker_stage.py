"""
SpeakerStage
- VAD 세그먼트를 pitch 기반으로 adult/child 라벨링
- 자극 후보(adult, 짧은 발화)와 아기 발화 후보(child)를 분리
"""

import logging

from app.config import get_settings
from app.models.speaker_splitter import SpeakerLabel, SpeakerSplitter
from app.pipeline.context import PipelineContext
from app.pipeline.stages.base_stage import BaseStage

logger = logging.getLogger(__name__)


class SpeakerStage(BaseStage):
    def __init__(self, splitter: SpeakerSplitter | None = None) -> None:
        self._settings = get_settings()
        self._splitter = splitter or SpeakerSplitter()

    @property
    def name(self) -> str:
        return "SpeakerStage"

    def validate(self, context: PipelineContext) -> str | None:
        if context.audio is None or context.sample_rate is None:
            return "audio/sample_rate가 필요합니다."
        if not context.speech_segments:
            return "speech_segments가 비어있습니다. VadStage가 먼저 실행되어야 합니다."
        return None

    def process(self, context: PipelineContext) -> None:
        labeled = self._splitter.label_segments(
            context.speech_segments,
            context.audio,
            int(context.sample_rate),
        )
        context.labeled_segments = labeled

        # stimulus candidates: adult & short enough
        stim = []
        child = []
        for ls in labeled:
            dur = ls.segment.duration_sec
            if ls.label == SpeakerLabel.ADULT and (
                self._settings.STIMULUS_MIN_SEC
                <= dur
                <= self._settings.STIMULUS_MAX_SEC
            ):
                stim.append(ls)
            elif ls.label == SpeakerLabel.CHILD and (
                self._settings.RESPONSE_MIN_SEC
                <= dur
                <= self._settings.RESPONSE_MAX_SEC
            ):
                child.append(ls)

        context.adult_stimuli_segments = sorted(stim, key=lambda x: x.segment.start_sec)
        context.child_segments = sorted(child, key=lambda x: x.segment.start_sec)

        logger.info(
            f"adult stimulus candidates={len(context.adult_stimuli_segments)}, "
            f"child segments={len(context.child_segments)}"
        )

        # 디버그 정보를 INFO로 출력하여 사용자 로그에서 확인 가능하게 함
        if context.adult_stimuli_segments:
            logger.info("Adult Segments:")
            for s in context.adult_stimuli_segments:
                logger.info(
                    f"  - [{s.segment.start_sec:.2f}-{s.segment.end_sec:.2f}s] "
                    f"F0={s.mean_f0_hz:.1f}Hz"
                )

        if context.child_segments:
            logger.info("Child Segments:")
            for s in context.child_segments:
                logger.info(
                    f"  - [{s.segment.start_sec:.2f}-{s.segment.end_sec:.2f}s] "
                    f"F0={s.mean_f0_hz:.1f}Hz"
                )
