import unittest
from unittest.mock import MagicMock

from app.models.speaker_splitter import LabeledSegment, SpeakerLabel
from app.models.vad import SpeechSegment
from app.pipeline.context import PipelineContext, RepResult, TrialResult
from app.pipeline.stages.imitation_judge_stage import ImitationJudgeStage


class TestImitationJudgeConsistency(unittest.TestCase):
    def setUp(self) -> None:
        self.stage = ImitationJudgeStage(scorer=MagicMock())
        # Mock settings
        self.stage._settings = MagicMock()
        self.stage._settings.TRIAL_DURATION_SEC = 8.0
        self.stage._settings.STIMULUS_SEARCH_WINDOW_SEC = 3.0
        self.stage._settings.RESPONSE_TIMEOUT_SEC = 5.0
        self.stage._settings.RESPONSE_MIN_SEC = 0.5
        self.stage._settings.CONSISTENCY_SEMITONE_THRESHOLD = 12.0
        self.stage._settings.DEBUG_OUT_DIR = None
        self.stage._settings.SIMILARITY_THRESHOLD = 0.5

        # Scorer mock
        self.stage._scorer.score.return_value = MagicMock(similarity=0.8)

    def _create_context(
        self, global_f0: float | None = None, cand_f0: float | None = None
    ) -> PipelineContext:
        ctx = PipelineContext(request_id="test")
        ctx.sample_rate = 16000
        ctx.audio = [0.0] * 16000 * 10  # 10s dummy

        # 1. Adult Stimulus (0-2s)
        ctx.adult_stimuli_segments = [
            LabeledSegment(
                segment=SpeechSegment(0.0, 2.0, 0, 32000),
                label=SpeakerLabel.ADULT,
                mean_f0_hz=200.0,
            )
        ]

        # 2. Child Segments for Global Stats
        # Create some background segments to set the global median
        child_segs = []
        if global_f0:
            # Add 3 segments with same F0 to strict median
            for i in range(3):
                child_segs.append(
                    LabeledSegment(
                        segment=SpeechSegment(
                            8.0 + i, 9.0 + i, 0, 0
                        ),  # Outside trial, just for stats
                        label=SpeakerLabel.CHILD,
                        mean_f0_hz=global_f0,
                    )
                )

        # 3. Candidate Segment (3.0 - 4.0s) -> Valid window
        cand_seg = LabeledSegment(
            segment=SpeechSegment(3.0, 4.0, 48000, 64000),
            label=SpeakerLabel.CHILD,
            mean_f0_hz=cand_f0,
        )
        child_segs.append(cand_seg)
        ctx.child_segments = child_segs

        # Trial Result setup
        tr = TrialResult(trial_index=0, stimulus_id="stim_0", stimulus_text="dummy")
        tr.repetitions.append(
            RepResult(
                rep_index=0, response_detected=False, success=False, latency_s=None
            )
        )
        ctx.trial_results.append(tr)

        return ctx

    def test_consistent_candidate(self) -> None:
        # Global 400, Cand 380 -> Diff < 12st -> Should Pass
        ctx = self._create_context(global_f0=400.0, cand_f0=380.0)

        self.stage.process(ctx)

        rep = ctx.trial_results[0].repetitions[0]
        # Should proceed to scoring => success (since similarity mocked to 0.8)
        self.assertTrue(rep.success, f"Failure Reason: {rep.failure_reason}")
        self.assertIsNone(rep.failure_reason)

    def test_inconsistent_candidate_low(self) -> None:
        # Global 400, Cand 180 (Adult-like) -> log2(180/400) = -1.15 oct = -13.8 st
        # |diff| > 12 -> Fail
        ctx = self._create_context(global_f0=400.0, cand_f0=180.0)

        self.stage.process(ctx)

        rep = ctx.trial_results[0].repetitions[0]
        self.assertFalse(rep.success)
        self.assertEqual(rep.failure_reason, "INCONSISTENT_RESPONSE")

    def test_inconsistent_candidate_high(self) -> None:
        # Global 400, Cand 900 -> log2(900/400) = 1.17 oct = 14 st -> Fail
        ctx = self._create_context(global_f0=400.0, cand_f0=900.0)

        self.stage.process(ctx)

        rep = ctx.trial_results[0].repetitions[0]
        self.assertFalse(rep.success)
        self.assertEqual(rep.failure_reason, "INCONSISTENT_RESPONSE")

    def test_no_global_stats(self) -> None:
        # No other child segments to form a median.
        # Only the candidate itself exists.
        # Median will be candidate's F0 (400). Diff is 0. Pass.

        ctx = self._create_context(global_f0=None, cand_f0=400.0)
        # Note: _create_context appends cand_seg to list.
        # So "child_f0_values" will contain [400]. Median = 400.

        self.stage.process(ctx)

        rep = ctx.trial_results[0].repetitions[0]
        self.assertTrue(rep.success)


if __name__ == "__main__":
    unittest.main()
