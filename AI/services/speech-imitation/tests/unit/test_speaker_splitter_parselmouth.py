import unittest
from unittest.mock import MagicMock, patch

import numpy as np
from app.models.speaker_splitter import SpeakerSplitter


class TestSpeakerSplitterParselmouth(unittest.TestCase):
    def setUp(self) -> None:
        self.splitter = SpeakerSplitter()
        # Mock settings
        self.splitter._settings = MagicMock()
        self.splitter._settings.PITCH_FMIN = 75.0
        self.splitter._settings.PITCH_FMAX = 600.0
        self.splitter._settings.PITCH_SQUEAL_HZ_THRESHOLD = 500.0

    def test_analyze_prosody_parselmouth_success(self) -> None:
        # Mock parselmouth module
        mock_parselmouth = MagicMock()
        mock_sound = MagicMock()
        mock_pitch = MagicMock()
        mock_point_process = MagicMock()
        mock_harmonicity = MagicMock()

        mock_parselmouth.Sound.return_value = mock_sound
        mock_sound.to_pitch.return_value = mock_pitch
        mock_sound.to_pitch.return_value = mock_pitch
        # mock_sound.to_point_process.return_value = mock_point_process -> Removed
        mock_sound.to_harmonicity.return_value = mock_harmonicity

        # Mock praat.call for To PointProcess
        mock_parselmouth.praat.call.return_value = mock_point_process

        # Pitch data
        real_array = np.array([300.0, 550.0, 0.0])
        mock_pitch.selected_array.__getitem__.side_effect = lambda k: (
            real_array if k == "frequency" else MagicMock()
        )

        # Jitter/Shimmer
        mock_point_process.get_jitter_local.return_value = 0.015
        mock_point_process.get_shimmer_local.return_value = 0.05

        # HNR
        # harmonicity.values returns numpy array
        mock_harmonicity.values = np.array([20.0, 22.0, -200.0, 18.0])

        with patch.dict("sys.modules", {"parselmouth": mock_parselmouth}):
            # Execution
            y = np.zeros(16000, dtype=np.float32)
            sr = 16000

            metrics = self.splitter._analyze_prosody(y, sr)

            # Verification
            # 1. Parselmouth called?
            mock_parselmouth.Sound.assert_called()
            mock_sound.to_pitch.assert_called()
            # mock_sound.to_point_process.assert_called() -> Removed
            mock_parselmouth.praat.call.assert_called()
            mock_sound.to_harmonicity.assert_called()

            # 2. Logic Check
            # Voiced: [300.0, 550.0]
            # Mean: (300+550)/2 = 425.0
            self.assertEqual(metrics["mean_f0"], 425.0)

            # Squeal: > 500.0. Only 550.0 is squeal. 1 out of 2 voiced. -> 0.5
            self.assertEqual(metrics["squeal_ratio"], 0.5)

            # Jitter/Shimmer
            self.assertEqual(metrics["jitter"], 0.015)
            self.assertEqual(metrics["shimmer"], 0.05)

            # HNR: (20+22+18)/3 = 20.0
            self.assertEqual(metrics["hnr"], 20.0)

            # MAD Check (sanity)
            self.assertIsNotNone(metrics["mad"])

    @patch("app.models.speaker_splitter._autocorr_pitch")
    def test_analyze_prosody_fallback(self, mock_autocorr: MagicMock) -> None:
        # Mock parselmouth to raise ImportError
        mock_parselmouth = MagicMock()
        mock_parselmouth.Sound.side_effect = ImportError("No parselmouth")

        with patch.dict("sys.modules", {"parselmouth": mock_parselmouth}):
            mock_autocorr.return_value = 200.0

            y = np.zeros(16000, dtype=np.float32)
            sr = 16000

            metrics = self.splitter._analyze_prosody(y, sr)

            # Should fallback
            self.assertEqual(metrics.get("mean_f0"), 200.0)
            self.assertIsNone(metrics.get("mad"))
            self.assertIsNone(metrics.get("jitter"))

    @patch("app.models.speaker_splitter.SpeakerSplitter._analyze_prosody")
    def test_label_segments_integration(self, mock_analyze: MagicMock) -> None:
        from app.models.vad import SpeechSegment

        # Setup
        mock_analyze.return_value = {
            "mean_f0": 400.0,
            "mad": 1.5,
            "squeal_ratio": 0.1,
            "jitter": 0.01,
            "shimmer": 0.05,
            "hnr": 20.0,
            "voiced_fraction": 0.8,
        }

        # Dummy segment (1 sec)
        # Assuming sample_rate=16000
        seg = SpeechSegment(
            start_sec=0.0, end_sec=1.0, start_sample=0, end_sample=16000
        )
        segments = [seg]
        audio = np.zeros(16000, dtype=np.float32)
        sr = 16000

        # Execution
        result = self.splitter.label_segments(segments, audio, sr)

        # Verification
        self.assertEqual(len(result), 1)
        r_seg = result[0]
        self.assertEqual(r_seg.mean_f0_hz, 400.0)
        self.assertEqual(r_seg.f0_mad_semitone, 1.5)
        self.assertEqual(r_seg.jitter_local, 0.01)
        self.assertEqual(r_seg.shimmer_local, 0.05)
        self.assertEqual(r_seg.hnr_db, 20.0)
        self.assertEqual(r_seg.voiced_fraction, 0.8)


if __name__ == "__main__":
    unittest.main()
