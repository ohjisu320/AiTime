"""
ImitationJudgeStage
- TrialPlan(자극 목록 x 3회 반복)을 실제 오디오 세그먼트에 매칭
- 엄마(ADULT) 자극 세그먼트 → 종료 후 RESPONSE_TIMEOUT 내 아기(CHILD) 세그먼트 탐색
- MFCC+DTW로 유사도 산출 후 threshold로 성공 판정
"""

import logging

from app.config import get_settings
from app.models.imitation_similarity import AudioSimilarityDTW
from app.pipeline.context import PipelineContext
from app.pipeline.stages.base_stage import BaseStage
from app.utils.audio import save_wav, slice_audio

logger = logging.getLogger(__name__)


class ImitationJudgeStage(BaseStage):
    def __init__(self, scorer: AudioSimilarityDTW | None = None) -> None:
        self._settings = get_settings()
        self._scorer = scorer or AudioSimilarityDTW()

    @property
    def name(self) -> str:
        return "ImitationJudgeStage"

    def validate(self, context: PipelineContext) -> str | None:
        if context.audio is None or context.sample_rate is None:
            return "audio/sample_rate가 필요합니다."
        if not context.trial_results:
            return (
                "trial_results가 비어있습니다. TrialPlanStage가 먼저 실행되어야 합니다."
            )
        return None

    def process(self, context: PipelineContext) -> None:
        adult_segs = context.adult_stimuli_segments
        child_segs = context.child_segments
        sr = int(context.sample_rate)

        if not adult_segs:
            context.add_warning(
                "adult stimulus candidates가 없습니다. (VAD/화자분리 실패 가능)"
            )
        if not child_segs:
            context.add_warning("child segments가 없습니다. (VAD/화자분리 실패 가능)")

        # 디버그: 세그먼트 타임스탬프 출력
        logger.debug(f"Adult segments ({len(adult_segs)}):")
        for i, seg in enumerate(adult_segs):
            logger.debug(
                f"  [{i}] {seg.segment.start_sec:.2f}-{seg.segment.end_sec:.2f}s"
            )
        logger.debug(f"Child segments ({len(child_segs)}):")
        for i, seg in enumerate(child_segs):
            logger.debug(
                f"  [{i}] {seg.segment.start_sec:.2f}-{seg.segment.end_sec:.2f}s"
            )

        # 8차 개선: 교차 할당(Alternating) 전략
        # Pitch 구분이 안 되므로, 모든 발화를 시간순으로 나열하고
        # Stimulus(0) -> Response(1) -> Stimulus(2) -> Response(3)... 순서로 강제 할당

        # 1) 모든 세그먼트 수집 (Config상 200Hz 이하가 없으므로 대부분 Child에 몰려있음)
        #    만약 Adult에도 일부 남아있다면 합쳐서 시간순 정렬 필요
        all_segs = []
        for s in adult_segs:
            all_segs.append(s.segment)
        for s in child_segs:
            all_segs.append(s.segment)

        # 시간순 정렬
        all_segs.sort(key=lambda x: x.start_sec)

        logger.info(f"Alternating Strategy: Total segments found = {len(all_segs)}")
        for i, s in enumerate(all_segs):
            logger.debug(f"  Seg {i}: {s.start_sec:.2f}-{s.end_sec:.2f}s")

        debug_dir = self._settings.DEBUG_OUT_DIR
        save_clips = bool(self._settings.SAVE_WAV_CLIPS) and debug_dir is not None

        if save_clips and debug_dir:
            import os

            os.makedirs(debug_dir, exist_ok=True)

        current_seg_idx = 0

        for t in context.trial_results:
            for r in t.repetitions:
                # 짝수 인덱스: Stimulus, 홀수 인덱스: Response
                if current_seg_idx + 1 >= len(all_segs):
                    # 더 이상 짝(Stim+Resp)을 지을 수 없음
                    r.failure_reason = (
                        "NO_STIMULUS"
                        if current_seg_idx >= len(all_segs)
                        else "NO_RESPONSE"
                    )
                    r.response_detected = False
                    r.success = False
                    logger.debug(
                        f"Trial {t.trial_index}: Not enough segments for pair "
                        f"(idx={current_seg_idx})"
                    )
                    continue

                # 강제 할당
                stim_seg = all_segs[current_seg_idx]
                resp_seg = all_segs[current_seg_idx + 1]
                current_seg_idx += 2  # 다음 쌍으로 이동

                # 정보 기록
                r.stimulus_time = (stim_seg.start_sec, stim_seg.end_sec)
                r.response_detected = True
                r.response_time = (resp_seg.start_sec, resp_seg.end_sec)
                r.latency_s = float(max(0.0, resp_seg.start_sec - stim_seg.end_sec))

                logger.debug(
                    f"Trial {t.trial_index}: Forced Match "
                    f"Stim[{stim_seg.start_sec:.2f}-{stim_seg.end_sec:.2f}] -> "
                    f"Resp[{resp_seg.start_sec:.2f}-{resp_seg.end_sec:.2f}]"
                )

                # 매칭 성공 처리 (유사도 계산 전 단계)
                # used_child_indices 등 불필요 로직 제거됨

                # 3) similarity
                stim_audio = slice_audio(
                    context.audio, sr, stim_seg.start_sec, stim_seg.end_sec
                )
                resp_audio = slice_audio(
                    context.audio, sr, resp_seg.start_sec, resp_seg.end_sec
                )

                sim_res = self._scorer.score(stim_audio, resp_audio, sr)
                r.similarity = float(sim_res.similarity)

                if sim_res.similarity >= float(self._settings.SIMILARITY_THRESHOLD):
                    r.success = True
                    r.failure_reason = None
                else:
                    r.success = False
                    r.failure_reason = "LOW_SIMILARITY"

                # 4) optional debug clips
                if save_clips:
                    success_mark = "OK" if r.success else "FAIL"
                    base = (
                        f"trial{t.trial_index:02d}_rep{r.rep_index:02d}_{success_mark}"
                    )
                    save_wav(f"{debug_dir}/{base}_stim.wav", stim_audio, sr)
                    save_wav(f"{debug_dir}/{base}_resp.wav", resp_audio, sr)

        # cleanup: NOT_EVALUATED remaining to None
        for t in context.trial_results:
            for r in t.repetitions:
                if r.failure_reason == "NOT_EVALUATED":
                    r.failure_reason = "NO_STIMULUS"
