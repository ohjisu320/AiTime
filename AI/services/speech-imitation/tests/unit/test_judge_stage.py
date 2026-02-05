import unittest
from unittest.mock import MagicMock

import numpy as np
from app.models.imitation_similarity import AudioSimilarityDTW, SimilarityResult
from app.models.speaker_splitter import LabeledSegment, SpeakerLabel
from app.models.vad import SpeechSegment
from app.pipeline.context import PipelineContext, RepResult, TrialResult
from app.pipeline.stages.imitation_judge_stage import ImitationJudgeStage


class TestJudgeStage(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_scorer = MagicMock(spec=AudioSimilarityDTW)
        # Default high similarity to isolate prosody logic
        self.mock_scorer.score.return_value = SimilarityResult(
            similarity=0.9, dtw_cost=0.1, used_frames_a=100, used_frames_b=100
        )
        self.stage = ImitationJudgeStage(scorer=self.mock_scorer)

        # Mock Context with dummy audio
        self.context = PipelineContext(
            request_id="test_req",
            audio=np.zeros(16000),  # 1 sec dummy audio
            sample_rate=16000,
        )
        self.context.trial_results = [
            TrialResult(
                trial_index=0,
                stimulus_id="s1",
                stimulus_text="mama",
                repetitions=[
                    RepResult(0, False, 0.0, False),
                    RepResult(1, False, 0.0, False),
                ],
            )
        ]

    def _create_segments(
        self, mean_f0_hz: float, mad_semitone: float
    ) -> tuple[LabeledSegment, LabeledSegment]:
        # Stimulus Segment (Adult)
        stim_seg = LabeledSegment(
            segment=SpeechSegment(0.0, 0.5, 0, 8000), label=SpeakerLabel.ADULT
        )
        # Response Segment (Child) with custom prosody
        resp_seg = LabeledSegment(
            segment=SpeechSegment(1.0, 1.5, 16000, 24000),
            label=SpeakerLabel.CHILD,
            mean_f0_hz=mean_f0_hz,
            f0_mad_semitone=mad_semitone,
            squeal_ratio=0.5,  # Irrelevant for this logic
        )
        return stim_seg, resp_seg

    def test_normal_prosody(self) -> None:
        # F0 < 450 (Normal Pitch) -> Should PASS based on similarity (0.9)
        stim, resp = self._create_segments(mean_f0_hz=350.0, mad_semitone=1.5)

        self.context.adult_stimuli_segments = [stim]
        self.context.child_segments = [resp]

        self.stage.process(self.context)

        rep = self.context.trial_results[0].repetitions[0]
        self.assertTrue(rep.success)
        self.assertIsNone(rep.failure_reason)

    def test_bad_prosody_monotone_squeal(self) -> None:
        # F0=500 (>450), MAD=0.5 (<1.0) -> BAD_PROSODY
        stim, resp = self._create_segments(mean_f0_hz=500.0, mad_semitone=0.5)

        self.context.adult_stimuli_segments = [stim]
        self.context.child_segments = [resp]

        self.stage.process(self.context)

        rep = self.context.trial_results[0].repetitions[0]
        self.assertFalse(rep.success)
        self.assertEqual(rep.failure_reason, "BAD_PROSODY")

    def test_bad_prosody_variable_squeal(self) -> None:
        # F0=500 (>450), MAD=3.0 (>2.0) -> BAD_PROSODY
        stim, resp = self._create_segments(mean_f0_hz=500.0, mad_semitone=3.0)

        self.context.adult_stimuli_segments = [stim]
        self.context.child_segments = [resp]

        self.stage.process(self.context)

        rep = self.context.trial_results[0].repetitions[0]
        self.assertFalse(rep.success)
        self.assertEqual(rep.failure_reason, "BAD_PROSODY")

    def test_high_pitch_normal_mad(self) -> None:
        # F0=500 (>450), MAD=1.5 (1.0~2.0) -> PASS (High pitch but normal intonation)
        stim, resp = self._create_segments(mean_f0_hz=500.0, mad_semitone=1.5)

        self.context.adult_stimuli_segments = [stim]
        self.context.child_segments = [resp]

        self.stage.process(self.context)

        rep = self.context.trial_results[0].repetitions[0]
        self.assertTrue(rep.success)
        self.assertIsNone(rep.failure_reason)

    def test_missing_prosody_data(self) -> None:
        # If F0 or MAD is None -> Should fallback to just similarity
        stim, resp = self._create_segments(mean_f0_hz=500.0, mad_semitone=1.5)
        resp.mean_f0_hz = None  # Missing

        self.context.adult_stimuli_segments = [stim]
        self.context.child_segments = [resp]

        self.stage.process(self.context)

        rep = self.context.trial_results[0].repetitions[0]
        self.assertTrue(rep.success)
