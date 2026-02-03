import logging
import unittest

import numpy as np
from app.models.speaker_splitter import SpeakerSplitter


class TestProsody(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.DEBUG)
        self.splitter = SpeakerSplitter()
        self.sr = 16000

    def test_squeal_detection(self) -> None:
        # 1. High frequency sine wave (500Hz) -> Should be Squeal
        duration = 1.0
        t = np.linspace(0, duration, int(self.sr * duration))
        # f = 500Hz
        y = np.sin(2 * np.pi * 500 * t)

        mean_f0, mad, squeal = self.splitter._analyze_prosody(y, self.sr)

        print(f"500Hz: Mean={mean_f0}, MAD={mad}, Squeal={squeal}")

        self.assertIsNotNone(mean_f0)
        self.assertGreater(mean_f0, 480)
        self.assertLess(mean_f0, 520)
        self.assertGreater(squeal, 0.9)  # Almost all frames > 450

    def test_normal_pitch(self) -> None:
        # 2. Normal pitch (300Hz) -> Squeal Ratio ~ 0
        duration = 1.0
        t = np.linspace(0, duration, int(self.sr * duration))
        y = np.sin(2 * np.pi * 300 * t)

        mean_f0, mad, squeal = self.splitter._analyze_prosody(y, self.sr)

        print(f"300Hz: Mean={mean_f0}, MAD={mad}, Squeal={squeal}")

        self.assertIsNotNone(mean_f0)
        self.assertLess(squeal, 0.1)

    def test_mad_variability(self) -> None:
        # 3. Frequency Modulated Signal (Vibrato)
        # Carrier 300Hz, Modulation 5Hz, Deviation 50Hz (250~350Hz)
        duration = 2.0
        t = np.linspace(0, duration, int(self.sr * duration))
        # Correct FM generation: integrate frequency
        instant_f = 300 + 50 * np.sin(2 * np.pi * 5 * t)
        phase = 2 * np.pi * np.cumsum(instant_f) / self.sr
        y = np.sin(phase)

        mean_f0, mad, squeal = self.splitter._analyze_prosody(y, self.sr)

        print(f"FM 300+/-50Hz: Mean={mean_f0}, MAD={mad}, Squeal={squeal}")

        # MAD should be significantly > 0
        self.assertIsNotNone(mad)
        self.assertGreater(mad, 0.5)

    def test_flat_mad(self) -> None:
        # 4. Perfectly flat 300Hz
        duration = 1.0
        t = np.linspace(0, duration, int(self.sr * duration))
        y = np.sin(2 * np.pi * 300 * t)

        mean_f0, mad, squeal = self.splitter._analyze_prosody(y, self.sr)
        print(f"Flat 300Hz: Mean={mean_f0}, MAD={mad}, Squeal={squeal}")

        # MAD should be very small
        if mad is not None:
            self.assertLess(mad, 0.5)


if __name__ == "__main__":
    unittest.main()
