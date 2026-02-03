# services/name_non_facing/app/pipeline/stages/__init__.py
"""
파이프라인 Stages 모듈

모든 Stage를 외부에 노출합니다.

Usage:
    from app.pipeline.stages import (
        InputStage,
        HeadDetectStage,   # YOLO 기반 (360°)
        TriggerStage,
        ChildAnalysisStage,
        ReactionDetectStage,
        ResultStage,
    )
    
    # [deprecated] MediaPipe 기반
    # from app.pipeline.stages import FaceDetectStage
"""

from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.stages.input_stage import InputStage
from app.pipeline.stages.trigger_stage import TriggerStage
from app.pipeline.stages.reaction_detect_stage import ReactionDetectStage
from app.pipeline.stages.result_stage import ResultStage
from app.pipeline.stages.head_detect_stage import HeadDetectStage
from app.pipeline.stages.child_analysis_stage import ChildAnalysisStage

# [deprecated] MediaPipe 기반 - lazy import (mediapipe 미설치 시 오류 방지)
def __getattr__(name):
    if name == "FaceDetectStage":
        from app.pipeline.stages.face_detect_stage import FaceDetectStage
        return FaceDetectStage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "BaseStage",
    "InputStage",
    "HeadDetectStage",      # YOLO 기반 (360°)
    "FaceDetectStage",      # [deprecated] MediaPipe 기반 (lazy import)
    "TriggerStage",
    "ChildAnalysisStage",
    "ReactionDetectStage",
    "ResultStage",
]
