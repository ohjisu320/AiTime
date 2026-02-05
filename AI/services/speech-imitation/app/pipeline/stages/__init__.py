"""
speech_imitation Pipeline Stages
"""

from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.stages.imitation_judge_stage import ImitationJudgeStage
from app.pipeline.stages.input_stage import InputStage
from app.pipeline.stages.result_stage import ResultStage
from app.pipeline.stages.speaker_stage import SpeakerStage
from app.pipeline.stages.trial_plan_stage import TrialPlanStage
from app.pipeline.stages.vad_stage import VadStage

__all__ = [
    "BaseStage",
    "InputStage",
    "VadStage",
    "SpeakerStage",
    "TrialPlanStage",
    "ImitationJudgeStage",
    "ResultStage",
]
