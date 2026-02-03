"""
파이프라인 컨텍스트

Stage 간 데이터 공유 및 최종 결과 포맷 생성.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

from app.models.speaker_splitter import LabeledSegment
from app.models.vad import SpeechSegment


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RepResult:
    rep_index: int
    response_detected: bool
    latency_s: float | None
    success: bool
    failure_reason: str | None = None
    similarity: float | None = None
    stimulus_time: tuple[float, float] | None = None
    response_time: tuple[float, float] | None = None
    child_mean_f0: float | None = None
    child_squeal_ratio: float | None = None
    child_mad_semitone: float | None = None


@dataclass
class TrialResult:
    trial_index: int
    stimulus_id: str
    stimulus_text: str
    repetitions: list[RepResult] = field(default_factory=list)


@dataclass
class PipelineContext:
    request_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    # input
    video_path: str | None = None
    age_months: int | None = None

    # derived
    age_band: str | None = None
    stimulus_set_id: str | None = None
    stimuli: list[str] = field(default_factory=list)

    # audio
    audio: np.ndarray | None = None
    sample_rate: int | None = None

    # intermediate
    speech_segments: list[SpeechSegment] = field(default_factory=list)
    labeled_segments: list[LabeledSegment] = field(default_factory=list)

    # selected segments for scoring
    adult_stimuli_segments: list[LabeledSegment] = field(default_factory=list)
    child_segments: list[LabeledSegment] = field(default_factory=list)

    # outputs
    trial_results: list[TrialResult] = field(default_factory=list)

    # meta
    status: PipelineStatus = PipelineStatus.PENDING
    processing_times: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    # Repro Keys
    code_sha: str | None = None
    config_version: str | None = None

    # Observability
    stage_metrics: dict[str, Any] = field(default_factory=dict)
    quality_flags: list[str] = field(default_factory=list)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_metric(self, stage: str, key: str, value: Any) -> None:
        if stage not in self.stage_metrics:
            self.stage_metrics[stage] = {}
        self.stage_metrics[stage][key] = value

    def add_flag(self, flag: str) -> None:
        if flag not in self.quality_flags:
            self.quality_flags.append(flag)

    def to_result(self) -> dict[str, Any]:
        # summary metrics
        total_trials = len(self.trial_results)
        reps = [r for t in self.trial_results for r in t.repetitions]
        total_reps = len(reps)
        success_reps = sum(1 for r in reps if r.success)
        success_trials = sum(
            1 for t in self.trial_results if any(r.success for r in t.repetitions)
        )

        # ADOS Scoring Logic
        # 1) A3: BAD_PROSODY ratio scores (0, 1, 2, 3) or 8 (No Response)
        detect_reps = [r for r in reps if r.response_detected]
        bad_prosody_count = sum(
            1 for r in detect_reps if r.failure_reason == "BAD_PROSODY"
        )

        ados_a3: int = 8
        if len(detect_reps) > 0:
            ratio = bad_prosody_count / len(detect_reps)
            if ratio == 0:
                ados_a3 = 0
            elif ratio <= 0.20:
                ados_a3 = 1
            elif ratio < 0.80:
                ados_a3 = 2
            else:
                ados_a3 = 3

        # 2) B18: Success Check
        # True: At least one success (Normal-ish)
        # False: All failed (Abnormal)
        # 사용자 요청: "하나라도 성공하면 True, 다 실패할 때만 False"
        ados_b18 = success_reps > 0

        return {
            "schema_version": self.extra.get("schema_version", "1.0"),
            "task_type": "SPEECH_IMITATION",
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat() + "Z",
            "age_months": self.age_months,
            "age_band": self.age_band,
            "stimulus_set_id": self.stimulus_set_id,
            "metrics": {
                "total_trials": total_trials,
                "repetitions_per_trial": self.extra.get("repetitions_per_trial", 3),
                "summary": {
                    "total_reps": total_reps,
                    "success_reps": success_reps,
                    "success_trials": success_trials,
                },
                "ADOS": {
                    "A3": ados_a3,
                    "B18": ados_b18,
                },
                "per_trial": [
                    {
                        "trial_index": t.trial_index,
                        "stimulus_id": t.stimulus_id,
                        "stimulus_text": t.stimulus_text,
                        "repetitions": [
                            {
                                "rep_index": r.rep_index,
                                "response_detected": r.response_detected,
                                "latency_s": r.latency_s,
                                "success": r.success,
                                "failure_reason": r.failure_reason,
                                "similarity": r.similarity,
                                "stimulus_time": r.stimulus_time,
                                "response_time": r.response_time,
                                "child_mean_f0": r.child_mean_f0,
                                "child_squeal_ratio": r.child_squeal_ratio,
                                "child_mad_semitone": r.child_mad_semitone,
                            }
                            for r in t.repetitions
                        ],
                    }
                    for t in self.trial_results
                ],
            },
            "status": self.status.value,
            "warnings": self.warnings,
            "error": self.error,
            "processing_times": self.processing_times,
            "repro": {
                "code_sha": self.code_sha,
                "config_version": self.config_version,
            },
            "observability": {
                "stage_metrics": self.stage_metrics,
                "quality_flags": self.quality_flags,
            },
        }
