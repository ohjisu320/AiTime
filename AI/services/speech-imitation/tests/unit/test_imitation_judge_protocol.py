import unittest
from unittest.mock import MagicMock

from app.models.speaker_splitter import LabeledSegment, SpeakerLabel
from app.models.vad import SpeechSegment
from app.pipeline.context import PipelineContext, RepResult, TrialResult
from app.pipeline.stages.imitation_judge_stage import ImitationJudgeStage


class TestImitationJudgeProtocol(unittest.TestCase):
    def setUp(self) -> None:
        self.stage = ImitationJudgeStage(scorer=MagicMock())

        # Mock settings
        self.stage._settings = MagicMock()
        self.stage._settings.TRIAL_DURATION_SEC = 8.0
        self.stage._settings.STIMULUS_SEARCH_WINDOW_SEC = 3.0
        self.stage._settings.RESPONSE_TIMEOUT_SEC = 5.0
        self.stage._settings.RESPONSE_MIN_SEC = 0.1
        self.stage._settings.SIMILARITY_THRESHOLD = 0.5
        self.stage._settings.PITCH_SQUEAL_HZ_THRESHOLD = 500.0
        self.stage._settings.PITCH_MAD_MONOTONE_THRESHOLD = 1.0
        self.stage._settings.PITCH_MAD_SONG_THRESHOLD = 2.0
        self.stage._settings.DEBUG_OUT_DIR = None
        self.stage._settings.SAVE_WAV_CLIPS = False

    def create_segment(
        self, start: float, end: float, label: SpeakerLabel
    ) -> LabeledSegment:
        # Dummy 16k samples/sec
        seg = SpeechSegment(
            start_sec=start,
            end_sec=end,
            start_sample=int(start * 16000),
            end_sample=int(end * 16000),
        )
        return LabeledSegment(
            segment=seg,
            label=label,
            mean_f0_hz=300.0 if label == SpeakerLabel.CHILD else 150.0,
            f0_mad_semitone=1.5,
            squeal_ratio=0.0,
        )

    def test_protocol_match_success(self) -> None:
        # Scenario: Ideal case
        # Trial 0 (0-8s)
        # Adult: 1.0 - 2.0s (Within search window 0-3s)
        # Child: 2.5 - 3.5s (Within response window 2.0 - 7.0s)

        ctx = PipelineContext(request_id="test_req")
        ctx.sample_rate = 16000
        ctx.audio = MagicMock()  # Mock audio array

        adult = self.create_segment(1.0, 2.0, SpeakerLabel.ADULT)
        child = self.create_segment(2.5, 3.5, SpeakerLabel.CHILD)

        ctx.adult_stimuli_segments = [adult]
        ctx.child_segments = [child]

        # Trial Results setup
        tr = TrialResult(
            trial_index=0,
            stimulus_id="S1",
            stimulus_text="Mamma",
            repetitions=[
                RepResult(
                    rep_index=0, response_detected=False, latency_s=None, success=False
                )
            ],
        )
        ctx.trial_results = [tr]

        # Mock Scorer
        mock_score = MagicMock()
        mock_score.similarity = 0.8
        self.stage._scorer.score.return_value = mock_score

        # execution
        self.stage.process(ctx)

        res = ctx.trial_results[0].repetitions[0]
        self.assertTrue(res.success)
        self.assertEqual(res.stimulus_time, (1.0, 2.0))
        self.assertEqual(res.response_time, (2.5, 3.5))
        self.assertEqual(res.failure_reason, None)

    def test_protocol_insufficient_stimulus(self) -> None:
        # Scenario: Adult speaks too late (4.0s) -> outside search window (0-3s)
        ctx = PipelineContext(request_id="test_req")
        ctx.sample_rate = 16000
        ctx.audio = MagicMock()

        adult = self.create_segment(4.0, 5.0, SpeakerLabel.ADULT)
        ctx.adult_stimuli_segments = [adult]
        ctx.child_segments = []

        tr = TrialResult(
            trial_index=0,
            stimulus_id="S1",
            stimulus_text="Mamma",
            repetitions=[
                RepResult(
                    rep_index=0, response_detected=False, latency_s=None, success=False
                )
            ],
        )
        ctx.trial_results = [tr]

        self.stage.process(ctx)

        res = ctx.trial_results[0].repetitions[0]
        self.assertFalse(res.success)
        self.assertEqual(res.failure_reason, "INSUFFICIENT_STIMULUS")

    def test_protocol_no_response(self) -> None:
        # Scenario: Adult OK, Child speaks too late
        # (matches next trial maybe, but not this one)
        # Adult: 1.0 - 2.0
        # Window: 2.0 - 7.0
        # Child: 7.5 - 8.5

        ctx = PipelineContext(request_id="test_req")
        ctx.sample_rate = 16000
        ctx.audio = MagicMock()

        adult = self.create_segment(1.0, 2.0, SpeakerLabel.ADULT)
        child = self.create_segment(7.5, 8.5, SpeakerLabel.CHILD)

        ctx.adult_stimuli_segments = [adult]
        ctx.child_segments = [child]

        tr = TrialResult(
            trial_index=0,
            stimulus_id="S1",
            stimulus_text="Mamma",
            repetitions=[
                RepResult(
                    rep_index=0, response_detected=False, latency_s=None, success=False
                )
            ],
        )
        ctx.trial_results = [tr]

        self.stage.process(ctx)

        res = ctx.trial_results[0].repetitions[0]
        self.assertFalse(res.success)
        # Since child starts > window_end or > trial_end, it's not a candidate
        self.assertEqual(res.failure_reason, "NO_RESPONSE")

    def test_protocol_overlap_clipping(self) -> None:
        # Scenario: Overlap
        # Adult: 1.0 - 3.0
        # Child: 2.5 - 3.5
        # Valid Region: max(2.5, 3.0) -> 3.0 to min(3.5, window_end)
        # Resulting Child Audio: 3.0 - 3.5 (0.5s duration)

        ctx = PipelineContext(request_id="test_req")
        ctx.sample_rate = 16000
        ctx.audio = MagicMock()

        adult = self.create_segment(1.0, 3.0, SpeakerLabel.ADULT)
        child = self.create_segment(2.5, 3.5, SpeakerLabel.CHILD)

        ctx.adult_stimuli_segments = [adult]
        ctx.child_segments = [child]

        tr = TrialResult(
            trial_index=0,
            stimulus_id="S1",
            stimulus_text="Mamma",
            repetitions=[
                RepResult(
                    rep_index=0, response_detected=False, latency_s=None, success=False
                )
            ],
        )
        ctx.trial_results = [tr]

        mock_score = MagicMock()
        mock_score.similarity = 0.8
        self.stage._scorer.score.return_value = mock_score

        self.stage.process(ctx)

        res = ctx.trial_results[0].repetitions[0]
        self.assertTrue(res.success)
        # Response time should be clipped start (3.0) to child end (3.5)
        self.assertEqual(res.response_time, (3.0, 3.5))


if __name__ == "__main__":
    unittest.main()
