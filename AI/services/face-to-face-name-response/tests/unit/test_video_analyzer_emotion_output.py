import unittest
from unittest.mock import patch

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


class TestVideoAnalyzerEmotionOutput(unittest.TestCase):
    @patch("app.rtn.pipeline.video_analyzer.WindowAnalyzer")
    @patch("app.rtn.pipeline.video_analyzer.SileroVAD")
    @patch("app.rtn.pipeline.video_analyzer.FaceDetectorMP")
    @patch("app.rtn.pipeline.video_analyzer.FaceMeshMP")
    @patch("app.rtn.pipeline.video_analyzer.vad_segments_from_video")
    def test_analyze_returns_emotion_data(
        self,
        mock_vad_segs,
        mock_facemesh,
        mock_detector,
        mock_vad,
        mock_window_analyzer,
    ) -> None:
        # Setup configs
        vad_cfg = VADConfig()
        face_cfg = FaceDetConfig()
        track_cfg = TrackConfig()
        role_cfg = RoleAssignConfig()
        roi_cfg = ROIConfig()
        gaze_cfg = GazeSmoothConfig()
        contact_cfg = ContactConfig()
        analysis_cfg = AnalysisConfig()
        emotion_cfg = EmotionConfig(enable=True)
        conf_th = 0.6

        # Setup mock behavior
        mock_vad_segs.return_value = [(0.0, 5.0)]  # One segment

        # Mock WindowAnalyzer instance
        mock_wa_instance = mock_window_analyzer.return_value

        # Mock CallResult with emotion data
        expected_distribution = {"happy": 0.8, "neutral": 0.2}
        expected_dominant = "happy"

        mock_call_result = CallResult(
            call_index=1,
            call_start=0.0,
            call_end=5.0,
            success=True,
            latency_s=1.0,
            gaze_duration_s=2.0,
            dominant_emotion=expected_dominant,
            emotion_distribution=expected_distribution,
        )
        mock_wa_instance.analyze_call.return_value = mock_call_result

        # Initialize VideoAnalyzer
        analyzer = VideoAnalyzer(
            vad_cfg,
            face_cfg,
            track_cfg,
            role_cfg,
            roi_cfg,
            gaze_cfg,
            contact_cfg,
            analysis_cfg,
            emotion_cfg,
            conf_th,
        )

        # Run analyze
        result = analyzer.analyze("dummy_video.mp4")

        # Verify output
        self.assertIn("per_call", result)
        self.assertEqual(len(result["per_call"]), 1)

        call_data = result["per_call"][0]
        self.assertIn("dominant_emotion", call_data)
        self.assertIn("emotion_distribution", call_data)

        self.assertEqual(call_data["dominant_emotion"], expected_dominant)
        self.assertEqual(call_data["emotion_distribution"], expected_distribution)


if __name__ == "__main__":
    unittest.main()
