import unittest

from app.models.schemas import (
    FailureCode,
    PairSchema,
    SegmentSchema,
    Severity,
    SpeakerLabel,
)


class TestSchemas(unittest.TestCase):
    def test_segment_schema_defaults(self) -> None:
        """Test SegmentSchema default values"""
        seg = SegmentSchema()
        self.assertIsInstance(seg.segment_id, str)
        self.assertEqual(seg.start_s, 0.0)
        self.assertEqual(seg.speaker_label, SpeakerLabel.UNKNOWN)
        self.assertIsNone(seg.energy_db)
        self.assertEqual(seg.quality_flags, [])

    def test_pair_schema_structure(self) -> None:
        """Test PairSchema correct structure including nested SegmentSchema"""
        stim_seg = SegmentSchema(
            start_s=1.0, end_s=2.0, speaker_label=SpeakerLabel.ADULT, energy_db=-20.0
        )

        pair = PairSchema(
            pair_id="trial_1_rep_1",
            trial_index=1,
            trial_start_s=0.0,
            trial_end_s=8.0,
            response_window_start_s=1.0,
            response_window_end_s=6.0,
            stimulus=stim_seg,
        )

        self.assertEqual(pair.pair_id, "trial_1_rep_1")
        self.assertEqual(pair.stimulus.speaker_label, SpeakerLabel.ADULT)
        self.assertIsNone(pair.response)
        self.assertEqual(pair.severity, Severity.PASS)

    def test_failure_code_definitions(self) -> None:
        """Ensure failure codes are defined correctly (sanity check)"""
        self.assertIn("NO_RESPONSE", FailureCode.__members__)
        self.assertIn("BAD_PROSODY", FailureCode.__members__)


if __name__ == "__main__":
    unittest.main()
