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

        # Protocol Timing
        # We assume session starts at 0.0s relative to audio beginning
        trial_duration = float(self._settings.TRIAL_DURATION_SEC)
        stim_search_win = float(self._settings.STIMULUS_SEARCH_WINDOW_SEC)
        resp_timeout = float(self._settings.RESPONSE_TIMEOUT_SEC)

        debug_dir = self._settings.DEBUG_OUT_DIR
        save_clips = bool(self._settings.SAVE_WAV_CLIPS) and debug_dir is not None

        if save_clips and debug_dir:
            import os

            os.makedirs(debug_dir, exist_ok=True)

        # Global Child F0 for Consistency Check (AI-408)
        import math
        import statistics

        child_f0_values = [s.mean_f0_hz for s in child_segs if s.mean_f0_hz is not None]
        global_child_f0 = (
            statistics.median(child_f0_values) if child_f0_values else None
        )
        if global_child_f0:
            logger.info(f"Global Child F0 Median: {global_child_f0:.1f} Hz")

        for t in context.trial_results:
            # Calculate fixed time slots for this trial
            # In a real scenario,
            # we might need 'session_start_time' offset if audio doesn't start at 0
            # Here we assume audio corresponds exactly to the session recording.
            trial_idx = t.trial_index  # 0-based
            trial_start_s = float(trial_idx * trial_duration)
            trial_end_s = trial_start_s + trial_duration

            # 1. Find Stimulus (Adult)
            # Search for the *first* adult segment that *starts*
            # within [trial_start, trial_start + stim_search_win]
            stim_candidate = None
            for seg in adult_segs:
                if (
                    seg.segment.start_sec >= trial_start_s
                    and seg.segment.start_sec < trial_start_s + stim_search_win
                ):
                    stim_candidate = seg
                    break  # Take the first one found

            # Setup repetitions (currently repetitions=1 per trial)
            for r in t.repetitions:
                if not stim_candidate:
                    r.failure_reason = "INSUFFICIENT_STIMULUS"
                    r.success = False
                    r.response_detected = False
                    logger.debug(
                        f"Trial {trial_idx}: No stimulus found in ",
                        f"[{trial_start_s}-{trial_start_s + stim_search_win}]",
                    )
                    continue

                stim_seg = stim_candidate.segment
                r.stimulus_time = (stim_seg.start_sec, stim_seg.end_sec)

                # 2. Response Window
                # Starts at Stimulus End.
                # Ends at min(Stimulus Start + Timeout, Trial End)
                # Note: Analysis Report said "Stimulus Onset + 5s"
                # but logical flow is usually "After Stimulus End".
                # Let's follow plan: "Window Start = Stimulus Start" (Onset Base)
                # But to avoid overlapping,
                # we only accept child segments that END after stimulus END.

                window_start = stim_seg.start_sec
                window_end = min(stim_seg.start_sec + resp_timeout, trial_end_s)

                # 3. Candidate Selection
                # Candidates must:
                # - Be labeled CHILD
                # (or UNKNOWN fallback if needed? For now strict CHILD)
                # - Start >= window_start (approx)
                # - Overlap with [stim_seg.end_sec, window_end] is positive

                candidates = []
                for c_seg in child_segs:
                    # Check overlap with the valid response region
                    # [stim_seg.end_sec, window_end]
                    # We want child speech *after* mom finishes,
                    # or at least mostly after.
                    # Strict Policy: Candidate must start AFTER Stimulus starts
                    if c_seg.segment.start_sec < window_start:
                        continue

                    # Must end before window_end? Or just start before window_end?
                    # Generally start before window_end.
                    if c_seg.segment.start_sec >= window_end:
                        continue

                    candidates.append(c_seg)

                if not candidates:
                    r.failure_reason = "NO_RESPONSE"
                    r.success = False
                    r.response_detected = False
                    logger.debug(f"Trial {trial_idx}: No child candidates in window")
                    continue

                # 4. Select Best Candidate & Clipping
                # Heuristic: Pick longest duration within the valid window? Or first?
                # Using "First valid" or "Longest" is common.
                # Let's use "Longest overlap with valid region".

                best_cand = max(
                    candidates,
                    key=lambda s: (
                        min(s.segment.end_sec, window_end)
                        - max(s.segment.start_sec, stim_seg.end_sec)
                    ),
                )

                # Consistency Check (AI-408)
                if global_child_f0 and best_cand.mean_f0_hz:
                    diff_semitone = 12.0 * math.log2(
                        best_cand.mean_f0_hz / global_child_f0
                    )
                    if abs(diff_semitone) > float(
                        self._settings.CONSISTENCY_SEMITONE_THRESHOLD
                    ):
                        r.failure_reason = "INCONSISTENT_RESPONSE"
                        r.success = False
                        r.response_detected = False
                        logger.debug(
                            f"Trial {trial_idx}: ",
                            f"Candidate rejected due to inconsistency "
                            f"(F0={best_cand.mean_f0_hz:.1f}Hz ",
                            f"vs Global={global_child_f0:.1f}Hz)",
                        )
                        continue

                # Clip
                # We only evaluate the portion AFTER stimulus ends (Strict no-overlap)
                valid_start = max(best_cand.segment.start_sec, stim_seg.end_sec)
                valid_end = min(best_cand.segment.end_sec, window_end)

                duration = valid_end - valid_start
                if duration < float(self._settings.RESPONSE_MIN_SEC):
                    r.failure_reason = (
                        "INSUFFICIENT_FEATURE_FRAMES"  # too short after clipping
                    )
                    r.success = False
                    r.response_detected = True  # Detected but too short
                    continue

                # Update Result with Clipped info?
                # The LabeledSegment has full audio metrics.
                # We might need to re-extract if we clip signal.
                # For now, we use the metrics of the *original full segment*
                # as approximation unless it's very different.
                # Ideally we slice audio -> extract prosody again.
                # But here we assume LabeledSegment is close enough.
                # EXCEPT mean_f0 etc might be wide.
                # Let's stick to using the LabeledSegment's metrics for now
                # to avoid re-running expensive pitch extraction in Python
                # (unless we use Parselmouth on clip).

                r.response_detected = True
                r.response_time = (valid_start, valid_end)
                r.latency_s = float(max(0.0, valid_start - stim_seg.end_sec))

                # Prosody Metrics
                r.child_mean_f0 = best_cand.mean_f0_hz
                r.child_squeal_ratio = best_cand.squeal_ratio
                r.child_mad_semitone = best_cand.f0_mad_semitone

                # New Metrics (AI-407B)
                # If they exist on LabeledSegment, mapping them would be great
                # but 'RepetitionResult' might not have fields yet.
                # The task AI-410 added 'SegmentSchema' but RepetitionResult is
                # defined in 'trial_stage.py' or 'schemas.py'?
                # Wait, 'schemas.py' defined 'PairSchema' but pipeline uses
                # 'TrialResult'/'RepetitionResult' objects from 'pipeline.context'.
                # We need to check if 'RepetitionResult' has slots for jitter/shimmer.
                # Assuming current codebase doesn't have them in
                # 'RepetitionResult' dataclass unless I added them.
                # I did NOT add them to RepetitionResult (only LabeledSegment).
                # So we just log them or ignore for now until schema update.

                logger.debug(
                    f"Trial {trial_idx}: Matched "
                    f"Stim[{stim_seg.start_sec:.2f}-{stim_seg.end_sec:.2f}] -> "
                    f"Resp[{valid_start:.2f}-{valid_end:.2f}] "
                    f"(Original: ",
                    f"{best_cand.segment.start_sec}-{best_cand.segment.end_sec})",
                )

                # 5. Evaluate Similarity (on Clipped Audio)
                stim_audio = slice_audio(
                    context.audio, sr, stim_seg.start_sec, stim_seg.end_sec
                )
                resp_audio = slice_audio(context.audio, sr, valid_start, valid_end)

                sim_res = self._scorer.score(stim_audio, resp_audio, sr)
                r.similarity = float(sim_res.similarity)

                # Prosody Check
                is_bad_prosody = False
                if r.child_mean_f0 is not None and r.child_mad_semitone is not None:
                    mad_min = float(self._settings.PITCH_MAD_MONOTONE_THRESHOLD)
                    mad_max = float(self._settings.PITCH_MAD_SONG_THRESHOLD)

                    # is_high_pitch = r.child_mean_f0 > squeal_th (Unused)
                    is_abnormal_mad = (r.child_mad_semitone < mad_min) or (
                        r.child_mad_semitone > mad_max
                    )
                    # Note: We removed the BAD_PROSODY *Gate* (auto-fail) in AI-407A,
                    # but we still mark the flag for information.
                    if is_abnormal_mad:
                        # Analysis Report said: "High pitch condition caused
                        # generic monotony check to be skipped"
                        # So we should check monotony regardless of pitch.
                        is_bad_prosody = True

                if sim_res.similarity >= float(self._settings.SIMILARITY_THRESHOLD):
                    r.success = True
                    r.failure_reason = "BAD_PROSODY" if is_bad_prosody else None
                else:
                    r.success = False
                    r.failure_reason = "LOW_SIMILARITY"

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
