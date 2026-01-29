"""
VadStage
- 전체 오디오에서 발화 구간 탐지
"""

import logging

from app.config import get_settings
from app.models.vad import VoiceActivityDetector
from app.pipeline.context import PipelineContext
from app.pipeline.stages.base_stage import BaseStage

logger = logging.getLogger(__name__)


class VadStage(BaseStage):
    def __init__(self, vad: VoiceActivityDetector | None = None) -> None:
        self._settings = get_settings()
        self._vad = vad or VoiceActivityDetector()

    @property
    def name(self) -> str:
        return "VadStage"

    def validate(self, context: PipelineContext) -> str | None:
        if context.audio is None or context.sample_rate is None:
            return (
                "audio/sample_rate가 필요합니다. InputStage가 먼저 실행되어야 합니다."
            )
        return None

    def process(self, context: PipelineContext) -> None:
        segs = self._vad.detect(context.audio, sample_rate=int(context.sample_rate))
        context.speech_segments = segs
        logger.info(f"VAD 세그먼트 수: {len(segs)}")

        # Observability
        total_speech = sum(s.duration_sec for s in segs)
        context.add_metric(self.name, "num_segments", len(segs))
        context.add_metric(self.name, "total_speech_sec", total_speech)

        if len(segs) == 0:
            context.add_flag("NO_SPEECH_DETECTED")
        elif total_speech < 0.5:
            context.add_flag("AUDIO_TOO_SHORT")
