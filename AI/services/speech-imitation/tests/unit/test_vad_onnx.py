import sys
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
from app.models.vad import OnnxSileroVAD

# Mock onnxruntime globally before importing vad
mock_ort = MagicMock()
sys.modules["onnxruntime"] = mock_ort


class TestOnnxVAD(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_onnx_initialization(self) -> None:
        # Test if session is created
        # We need to ensure OnnxSileroVAD tries to use our mock
        # Since we patched sys.modules,
        # import onnxruntime inside vad.py will return mock_ort

        # We must mock os.path.exists to return True for the model file
        with patch("os.path.exists", return_value=True):
            vad = OnnxSileroVAD("dummy/path.onnx")

        mock_ort.InferenceSession.assert_called()
        self.assertIsNotNone(vad.session)

    def test_timestamp_logic(self) -> None:
        # Test get_speech_timestamps logic by mocking __call__

        with patch("os.path.exists", return_value=True):
            vad = OnnxSileroVAD("dummy.onnx")

        # Mock __call__ to return high probability for middle chunks
        # Total audio: 3 chunks (3 * 512 = 1536 samples)
        # Probs: [0.1, 0.9, 0.1]
        # Expect speech in middle chunk

        def mock_inference(
            x: np.ndarray, sr: int
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
            # x shape (1, 512)
            # return shape (1, 1) ? No, typically (1, 1) output for Silero
            # We used out[0][0] in code
            # We need to track which chunk we are on?
            # Start state tracking manually?
            pass

        # Easier: mock vad.session.run
        # The code loop:
        # for chunk in chunks:
        #    out = self(chunk, sr) -> session.run

        # We need to mock session.run to return specific values in sequence
        vad.session = MagicMock()

        # Output format of session.run is [output, h_new, c_new]
        # We only care about output

        # Scenarios:
        # 1. Silence (0.1)
        # 2. Speech (0.9)
        # 3. Speech (0.8)
        # 4. Silence (0.1)

        side_effects = [
            (np.array([[0.1]]), np.zeros((2, 1, 64)), np.zeros((2, 1, 64))),
            (np.array([[0.9]]), np.zeros((2, 1, 64)), np.zeros((2, 1, 64))),
            (np.array([[0.8]]), np.zeros((2, 1, 64)), np.zeros((2, 1, 64))),
            (np.array([[0.1]]), np.zeros((2, 1, 64)), np.zeros((2, 1, 64))),
        ]
        vad.session.run.side_effect = side_effects

        audio = np.zeros(512 * 4, dtype=np.float32)
        sr = 16000

        # Settings: threshold=0.5
        timestamps = vad.get_speech_timestamps(
            audio,
            sr,
            threshold=0.5,
            min_speech_duration_ms=0,  # Allow short speech for test
            min_silence_duration_ms=0,
            speech_pad_ms=0,
        )

        # Expect speech from chunk 1 start to chunk 2 end (approx)
        # Chunk 0: 0.1 -> Silence
        # Chunk 1: 0.9 -> Speech Start (at 512)
        # Chunk 2: 0.8 -> Speech Continue
        # Chunk 3: 0.1 -> Speech End (at 1536?)

        # Because implemented logic:
        # if prob >= threshold and not triggered: triggered=True, start=current
        # if prob < threshold-0.15 and triggered: end=temp_end?

        # Let's trace loop:
        # i=0 (0): 0.1. Not triggered.
        # i=1 (512): 0.9. Triggered. start=512.
        # i=2 (1024): 0.8. Triggered.
        # i=3 (1536): 0.1. < 0.35. Triggered. temp_end set to 1536.
        #   (current_time - temp_end) check?
        #   In my code:
        #   if (prob < threshold - 0.15) and triggered:
        #       if not temp_end: temp_end = current_time (1536)
        #       if (current_time - temp_end) < min_silence: continue
        #       else: speech_end = temp_end ...

        # If min_silence is 0, it should cut immediately?
        # Verify result

        # With min_speech=0, min_silence=0

        self.assertEqual(len(timestamps), 1)
        ts = timestamps[0]
        self.assertEqual(ts["start"], 512)
        # Because at i=3 (1536), prob drop.
        # temp_end became 1536.
        # loop finishes.
        # If loop finishes with triggered, we append?
        # In my code: "Check last segment if triggered".
        # Yes.

        # Wait, inside loop at i=3:
        # temp_end = 1536.
        # min_silence=0.
        # (1536 - 1536) < 0? No. 0 < 0 is False.
        # So it processes end.

        self.assertEqual(ts["end"], 1536)


if __name__ == "__main__":
    unittest.main()
