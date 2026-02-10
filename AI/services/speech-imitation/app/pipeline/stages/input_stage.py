"""
InputStage
- 비디오 경로에서 오디오 추출/로드
"""

import logging
from pathlib import Path

from app.config import get_settings
from app.pipeline.context import PipelineContext
from app.pipeline.stages.base_stage import BaseStage
from app.utils.audio import load_audio_from_video

logger = logging.getLogger(__name__)


class InputStage(BaseStage):
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "InputStage"

    def validate(self, context: PipelineContext) -> str | None:
        if not context.video_path:
            return "video_path가 필요합니다."
        if not Path(context.video_path).exists():
            return f"비디오 파일이 존재하지 않습니다: {context.video_path}"
        return None

    def process(self, context: PipelineContext) -> None:
        audio, sr, _ = load_audio_from_video(
            context.video_path,
            sample_rate=int(self._settings.SAMPLE_RATE),
            mono=bool(self._settings.MONO),
            keep_audio_file=False,
        )
        context.audio = audio
        context.sample_rate = sr
        logger.info(f"오디오 로드 완료: samples={len(audio)}, sr={sr}")
