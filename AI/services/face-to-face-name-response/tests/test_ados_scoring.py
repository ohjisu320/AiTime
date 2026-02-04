import os
import sys
import unittest
from unittest.mock import patch

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    EmotionConfig,
    FaceDetConfig,
    GazeSmoothConfig,
    ROIConfig,
    RoleAssignConfig,
    TrackConfig,
    VADConfig,
)
from app.rtn.pipeline.results import CallResult
from app.rtn.pipeline.video_analyzer import VideoAnalyzer


class TestADOSScoring(unittest.TestCase):
    def setUp(self) -> None:
        self.vad_cfg = VADConfig()
        self.face_cfg = FaceDetConfig()
        self.track_cfg = TrackConfig()
        self.role_cfg = RoleAssignConfig()
        self.roi_cfg = ROIConfig()
        self.gaze_cfg = GazeSmoothConfig()
        self.contact_cfg = ContactConfig()
        self.analysis_cfg = AnalysisConfig()
        self.emotion_cfg = EmotionConfig()

    def create_analyzer(self) -> VideoAnalyzer:
        with (
            patch("app.rtn.pipeline.video_analyzer.SileroVAD"),
            patch("app.rtn.pipeline.video_analyzer.FaceDetectorMP"),
            patch("app.rtn.pipeline.video_analyzer.FaceMeshMP"),
            patch("app.rtn.pipeline.video_analyzer.WindowAnalyzer"),
        ):
            analyzer = VideoAnalyzer(
                self.vad_cfg,
                self.face_cfg,
                self.track_cfg,
                self.role_cfg,
                self.roi_cfg,
                self.gaze_cfg,
                self.contact_cfg,
                self.analysis_cfg,
                self.emotion_cfg,
                0.6,
            )
            return analyzer

    def test_ados_scoring_scenario_1(self) -> None:
        """
        Scenario 1:
        - 3 Calls, all successful.
        - Emotions: Happiness, Surprise, Anger (3 unique).
        - Happiness present.

        Expected:
        - B1: 3 (3 successes)
        - B4: 0 (3 unique emotions -> Score 0)
        - B6: True (Happiness found)
        - B18: True (Success > 0)
        """
        analyzer = self.create_analyzer()

        with patch(
            "app.rtn.pipeline.video_analyzer.vad_segments_from_video"
        ) as mock_vad:
            mock_vad.return_value = [(0, 1), (2, 3), (4, 5)]

            r1 = CallResult(
                1,
                0,
                1,
                True,
                0.5,
                1.0,
                "Happiness",
                {},
                directional_emotions=["Happiness"],
                has_happiness=True,
            )
            r2 = CallResult(
                2,
                2,
                3,
                True,
                0.5,
                1.0,
                "Surprise",
                {},
                directional_emotions=["Surprise"],
                has_happiness=False,
            )
            r3 = CallResult(
                3,
                4,
                5,
                True,
                0.5,
                1.0,
                "Anger",
                {},
                directional_emotions=["Anger"],
                has_happiness=False,
            )

            analyzer.window_analyzer.analyze_call.side_effect = [r1, r2, r3]

            result = analyzer.analyze("dummy_path")
            ados = result["ADOS"]

            print(f"Scenario 1 Result: {ados}")
            self.assertEqual(ados["B1"], 3)
            self.assertEqual(ados["B4"], 0)
            self.assertTrue(ados["B6"])
            self.assertTrue(ados["B18"])

    def test_ados_scoring_scenario_2(self) -> None:
        """
        Scenario 2:
        - 2 Calls, 1 success.
        - Emotions: Neutral only.
        - No Happiness.

        Expected:
        - B1: 1 (1 success)
        - B4: 3 (0 unique emotions non-Neutral -> Score 3)
        - B6: False
        - B18: True (Success > 0)
        """
        analyzer = self.create_analyzer()

        with patch(
            "app.rtn.pipeline.video_analyzer.vad_segments_from_video"
        ) as mock_vad:
            mock_vad.return_value = [(0, 1), (2, 3)]

            r1 = CallResult(
                1,
                0,
                1,
                True,
                0.5,
                1.0,
                "Neutral",
                {},
                directional_emotions=["Neutral"],
                has_happiness=False,
            )
            r2 = CallResult(
                2,
                2,
                3,
                False,
                None,
                0.0,
                None,
                {},
                directional_emotions=[],
                has_happiness=False,
            )

            analyzer.window_analyzer.analyze_call.side_effect = [r1, r2]

            result = analyzer.analyze("dummy_path")
            ados = result["ADOS"]

            print(f"Scenario 2 Result: {ados}")
            self.assertEqual(ados["B1"], 1)
            self.assertEqual(ados["B4"], 3)
            self.assertFalse(ados["B6"])
            self.assertTrue(ados["B18"])

    def test_ados_scoring_scenario_3(self) -> None:
        """
        Scenario 3:
        - 4 Calls, 2 success.
        - Emotions: Anger, Anger (1 unique).
        - No Happiness.

        Expected:
        - B1: 2 (2 success, capped at 3 if more) -> wait, B1 maps success count exactly?
          User said: 0->0, 1->1, 2->2, 3->3.
          My code: min(3, success_count).
          So 2 success -> 2.
        - B4: 2 (1 unique emotion -> Score 2)
        - B6: False
        - B18: True
        """
        analyzer = self.create_analyzer()

        with patch(
            "app.rtn.pipeline.video_analyzer.vad_segments_from_video"
        ) as mock_vad:
            mock_vad.return_value = [(0, 1), (1, 2), (2, 3), (3, 4)]

            r1 = CallResult(
                1,
                0,
                1,
                True,
                0.5,
                1.0,
                "Anger",
                {},
                directional_emotions=["Anger"],
                has_happiness=False,
            )
            r2 = CallResult(
                2,
                1,
                2,
                True,
                0.5,
                1.0,
                "Anger",
                {},
                directional_emotions=["Anger"],
                has_happiness=False,
            )
            r3 = CallResult(
                3,
                2,
                3,
                False,
                None,
                0.0,
                None,
                {},
                directional_emotions=[],
                has_happiness=False,
            )
            r4 = CallResult(
                4,
                3,
                4,
                False,
                None,
                0.0,
                None,
                {},
                directional_emotions=[],
                has_happiness=False,
            )

            analyzer.window_analyzer.analyze_call.side_effect = [r1, r2, r3, r4]

            result = analyzer.analyze("dummy_path")
            ados = result["ADOS"]

            print(f"Scenario 3 Result: {ados}")
            self.assertEqual(ados["B1"], 2)
            self.assertEqual(ados["B4"], 2)
            self.assertFalse(ados["B6"])
            self.assertTrue(ados["B18"])


if __name__ == "__main__":
    unittest.main()
