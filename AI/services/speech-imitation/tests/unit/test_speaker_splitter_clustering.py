import unittest
from unittest.mock import MagicMock
import numpy as np

from app.models.speaker_splitter import SpeakerSplitter, SpeakerLabel
from app.models.vad import SpeechSegment


class TestSpeakerSplitterClustering(unittest.TestCase):
    def setUp(self):
        self.splitter = SpeakerSplitter()
        self.splitter._settings = MagicMock()
        self.splitter._settings.PITCH_CHILD_HZ_THRESHOLD = 200.0
        self.splitter._settings.ENABLE_DYNAMIC_THRESHOLD = True
        self.splitter._settings.MIN_CLUSTERING_SAMPLES = 3
        # Mock analyze_prosody to return predictable values
        self.splitter._analyze_prosody = MagicMock()

    def test_clustering_distinct_speakers(self):
        # Scenario: 3 Adult (Low) and 3 Child (High)
        # Adult: ~150Hz
        # Child: ~400Hz
        # Expect Threshold approx (150+400)/2 = 275Hz

        f0_values = [140.0, 150.0, 160.0, 390.0, 400.0, 410.0]

        # Internal test of _calculate_dynamic_threshold
        th = self.splitter._calculate_dynamic_threshold(f0_values)
        self.assertIsNotNone(th)
        self.assertTrue(250.0 < th < 300.0, f"Threshold {th} should be around 275")

    def test_clustering_unimodal_fallback(self):
        # Scenario: All Adult (~150Hz). Variance small.
        f0_values = [145.0, 150.0, 155.0, 148.0, 152.0]

        th = self.splitter._calculate_dynamic_threshold(f0_values)
        # Should fallback because centroids will be very close
        self.assertIsNone(th, "Should return None for unimodal distribution")

    def test_clustering_not_enough_samples(self):
        f0_values = [150.0, 400.0]  # Only 2 samples
        self.splitter._settings.MIN_CLUSTERING_SAMPLES = 3

        th = self.splitter._calculate_dynamic_threshold(f0_values)
        self.assertIsNone(th)

    def test_integration_label_segments(self):
        # Mock _analyze_prosody to return specific F0s for segments
        # 3 Segments: 150, 400, 160
        # Expected:
        # Dynamic Th calc on [150, 400, 160] -> ~275Hz
        # Seg 1 (150) -> ADULT
        # Seg 2 (400) -> CHILD
        # Seg 3 (160) -> ADULT

        segments = [
            SpeechSegment(start_sec=0, end_sec=1, start_sample=0, end_sample=16000),
            SpeechSegment(start_sec=1, end_sec=2, start_sample=16000, end_sample=32000),
            SpeechSegment(start_sec=2, end_sec=3, start_sample=32000, end_sample=48000),
        ]

        # Side effect for _analyze_prosody
        def side_effect(y, sr):
            # Hack: Identify segment by length or just sequence?
            # Since mock is called in order...
            pass

        # Better: use side_effect with an iterator
        outputs = [
            {"mean_f0": 150.0},
            {"mean_f0": 400.0},
            {"mean_f0": 160.0},
        ]
        self.splitter._analyze_prosody.side_effect = outputs

        audio = np.zeros(48000)  # Dummy audio

        labeled = self.splitter.label_segments(segments, audio, 16000)

        self.assertEqual(len(labeled), 3)
        self.assertEqual(labeled[0].label, SpeakerLabel.ADULT)
        self.assertEqual(labeled[1].label, SpeakerLabel.CHILD)
        self.assertEqual(labeled[2].label, SpeakerLabel.ADULT)

        # Verify threshold applied was dynamic (implied by ADULT label for 160Hz,
        # though 160 < 200 static is also ADULT.
        # But if we had [250(Adult), 400(Child)] vs Static 200...
        # Let's try a case where Static would fail.

    def test_clustering_overrides_static(self):
        # Scenario: High-pitched Mom (250Hz) vs Child (450Hz).
        # Static Threshold = 200Hz.
        # If Static: Mom (250) -> CHILD (Wrong)
        # If Dynamic: Cluster [250, 250, 260, 450, 460, 450].
        # Centroids ~253 and ~453. Threshold ~353.
        # Mom (250) < 353 -> ADULT (Correct)

        outputs = [
            {"mean_f0": 250.0},
            {"mean_f0": 260.0},
            {"mean_f0": 255.0},
            {"mean_f0": 450.0},
            {"mean_f0": 460.0},
            {"mean_f0": 455.0},
        ]
        self.splitter._analyze_prosody.side_effect = outputs

        segments = [SpeechSegment(0, 1, 0, 100) for _ in range(6)]
        audio = np.zeros(600)

        labeled = self.splitter.label_segments(segments, audio, 16000)

        # First 3 should be ADULT despite being > 200Hz
        for i in range(3):
            self.assertEqual(
                labeled[i].label,
                SpeakerLabel.ADULT,
                f"Seg {i} (High Pitch Mom) should be ADULT with dynamic threshold",
            )

        # Last 3 should be CHILD
        for i in range(3, 6):
            self.assertEqual(labeled[i].label, SpeakerLabel.CHILD)


if __name__ == "__main__":
    unittest.main()
