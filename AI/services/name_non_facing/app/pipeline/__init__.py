# services/name_non_facing/app/pipeline/__init__.py
"""
파이프라인 모듈

오디오/비전 분석 파이프라인을 제공합니다.

Usage:
    from app.pipeline import create_audio_pipeline
    
    pipeline = create_audio_pipeline()
    result = pipeline.run(
        video_path="sample.mp4",
        child_name="동한"
    )
    
    # 결과 확인
    for trial in result["metrics"]["per_trial"]:
        print(f"시도 {trial['trial_index']}: {'성공' if trial['success'] else '실패'}")
"""

from app.pipeline.context import (
    PipelineContext,
    PipelineStatus,
    TrialResult,
)
from app.pipeline.orchestrator import (
    AudioPipelineOrchestrator,
    create_audio_pipeline,
)
from app.pipeline.stages import (
    BaseStage,
    InputStage,
    TriggerStage,
    ReactionDetectStage,
    ResultStage,
)

__all__ = [
    # Context
    "PipelineContext",
    "PipelineStatus",
    "TrialResult",
    # Orchestrator
    "AudioPipelineOrchestrator",
    "create_audio_pipeline",
    # Stages
    "BaseStage",
    "InputStage",
    "TriggerStage",
    "ReactionDetectStage",
    "ResultStage",
]