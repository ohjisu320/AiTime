import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.rtn.config import EmotionConfig

# We import the Class, but the init logic runs later,
# so we can patch sys.modules before init (if we create instance there)
from app.rtn.emotion.emotion_recognizer import EmotionRecognizer


class TestEmotionRecognizer(unittest.TestCase):
    def test_predict_success(self) -> None:
        # Setup mock module
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_module.HSEmotionRecognizer = mock_class

        # Setup instance mock
        mock_instance = mock_class.return_value
        mock_scores = [0.01, 0.01, 0.01, 0.01, 0.9, 0.05, 0.0, 0.01]
        mock_instance.predict_emotions.return_value = ("Happiness", mock_scores)

        # Patch sys.modules to simulate hsemotion.facial_emotions existence
        with patch.dict(
            sys.modules,
            {"hsemotion": MagicMock(), "hsemotion.facial_emotions": mock_module},
        ):
            cfg = EmotionConfig(enable=True, model_name="test_model")
            recognizer = EmotionRecognizer(cfg)

            # Act
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            result = recognizer.predict(frame)

            # Assert
            self.assertIsNotNone(result)
            self.assertEqual(len(result), 8)
            self.assertAlmostEqual(result["Happiness"], 0.9)

    def test_disabled_config(self) -> None:
        cfg = EmotionConfig(enable=False)
        recognizer = EmotionRecognizer(cfg)
        self.assertFalse(recognizer.enabled)
        self.assertIsNone(recognizer.predict(np.zeros((10, 10, 3), dtype=np.uint8)))

    def test_import_error_handling(self) -> None:
        # Simulate import error
        # We need to ensure hsemotion is NOT in sys.modules or raises ImportError
        # Since patch.dict restores, we can set it to a mock
        # that raises ImportError on access?
        # Or just ensure it's not there.
        # But earlier tests might have polluted sys.modules?
        # patch.dict handles restoration.

        # The code does: from hsemotion.facial_emotions import ...
        # We can make that raise ImportError by setting side_effect on the module usage?
        # A simpler way is to patch builtins.__import__ but that's complex.
        # Or simply make sure 'hsemotion' is not in sys.modules.

        with patch.dict(sys.modules):
            # Remove if exists
            if "hsemotion.facial_emotions" in sys.modules:
                del sys.modules["hsemotion.facial_emotions"]
            if "hsemotion" in sys.modules:
                del sys.modules["hsemotion"]

            # Also need to prevent it from being found.
            # We can mock sys.modules such that it raises ImportError?
            # No, sys.modules is a dict.
            # The easiest way to force ImportError
            # for a specific module is to set it to None in sys.modules (in Py3).
            sys.modules["hsemotion"] = None
            sys.modules["hsemotion.facial_emotions"] = None

            # However, if it's None, it raises ModuleNotFoundError.
            # My code catches ImportError (which MNE inherits from).

            cfg = EmotionConfig(enable=True)
            recognizer = EmotionRecognizer(cfg)

            self.assertFalse(recognizer.enabled)


if __name__ == "__main__":
    unittest.main()
