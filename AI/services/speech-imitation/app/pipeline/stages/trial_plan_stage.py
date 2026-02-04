"""
TrialPlanStage
- 월령(age_months)에 따라 stimulus_set 선택
- stimulus 목록 기반으로 trial(자극) x repetitions(3) 구조 생성
"""

import logging

from app.config import AgeBand, get_settings
from app.pipeline.context import PipelineContext, RepResult, TrialResult
from app.pipeline.stages.base_stage import BaseStage

logger = logging.getLogger(__name__)


class TrialPlanStage(BaseStage):
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "TrialPlanStage"

    def validate(self, context: PipelineContext) -> str | None:
        if context.age_months is None:
            return "age_months가 필요합니다. (12~23개월)"
        if context.age_months < 12 or context.age_months > 23:
            return f"지원 월령 범위(12~23개월) 밖입니다: {context.age_months}"
        return None

    def process(self, context: PipelineContext) -> None:
        age = int(context.age_months)
        if 12 <= age <= 17:
            band = AgeBand.M12_17.value
            stimuli = list(self._settings.STIMULI_M12_17)
            ssid = self._settings.STIMULUS_SET_ID_M12_17
        else:
            band = AgeBand.M18_23.value
            stimuli = list(self._settings.STIMULI_M18_23)
            ssid = self._settings.STIMULUS_SET_ID_M18_23

        context.age_band = band
        context.stimulus_set_id = ssid
        context.stimuli = stimuli

        reps_per = int(self._settings.REPETITIONS_PER_TRIAL)
        context.extra["repetitions_per_trial"] = reps_per

        trial_results = []
        for i, stim in enumerate(stimuli, start=1):
            trial_id = f"VI{band.split('_')[0][1:]}_{i:02d}"  # e.g., VI12_01 (휴리스틱)
            tr = TrialResult(trial_index=i, stimulus_id=trial_id, stimulus_text=stim)
            # 자리만 만들어 두고, 실제 매칭은 ImitationJudgeStage에서 수행
            for r in range(1, reps_per + 1):
                tr.repetitions.append(
                    RepResult(
                        rep_index=r,
                        response_detected=False,
                        latency_s=None,
                        success=False,
                        failure_reason="NOT_EVALUATED",
                    )
                )
            trial_results.append(tr)

        context.trial_results = trial_results
        logger.info(
            f"trial plan 생성: trials={len(trial_results)} reps/trial={reps_per}"
        )
