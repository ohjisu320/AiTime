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

        mock_parselmouth.Sound.return_value = mock_sound
        mock_sound.to_pitch.return_value = mock_pitch

        # pitch.selected_array["frequency"] returns the numpy array
        # So we mock __getitem__ of selected_array to return our array
        # when called with "frequency"
        real_array = np.array([300.0, 550.0, 0.0])
        mock_pitch.selected_array.__getitem__.side_effect = lambda k: (
            real_array if k == "frequency" else MagicMock()
        )

        with patch.dict("sys.modules", {"parselmouth": mock_parselmouth}):
            # Execution
            # dummy audio
            y = np.zeros(16000, dtype=np.float32)
            sr = 16000

            mean_f0, mad, squeal_ratio = self.splitter._analyze_prosody(y, sr)

            # Verification
            # 1. Parselmouth called?
            mock_parselmouth.Sound.assert_called()
            # args, kwargs = mock_parselmouth.Sound.call_args
            # np.testing.assert_array_equal(args[0], y)  # Optional: strict check
            mock_sound.to_pitch.assert_called()

            # 2. Logic Check
            # Voiced: [300.0, 550.0]
            # Mean: (300+550)/2 = 425.0
            self.assertEqual(mean_f0, 425.0)

            # Squeal: > 500.0. Only 550.0 is squeal. 1 out of 2 voiced. -> 0.5
            self.assertEqual(squeal_ratio, 0.5)

            # MAD Check (sanity)
            self.assertIsNotNone(mad)

    @patch("app.models.speaker_splitter._autocorr_pitch")
    def test_analyze_prosody_fallback(self, mock_autocorr: MagicMock) -> None:
        # Mock parselmouth to raise ImportError
        mock_parselmouth = MagicMock()
        mock_parselmouth.Sound.side_effect = ImportError("No parselmouth")

        with patch.dict("sys.modules", {"parselmouth": mock_parselmouth}):
            mock_autocorr.return_value = 200.0

            y = np.zeros(16000, dtype=np.float32)
            sr = 16000

            mean_f0, mad, squeal = self.splitter._analyze_prosody(y, sr)

            # Should fallback
            self.assertEqual(mean_f0, 200.0)
            self.assertIsNone(mad)
            self.assertIsNone(squeal)


if __name__ == "__main__":
    unittest.main()
