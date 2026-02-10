
import os
import sys
import unittest
import numpy as np
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path so we can import app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.pipeline.analyzer import MotionAnalyzer, ACTION_NOT_DETECTED

class TestAnalyzerRegression(unittest.TestCase):
    def setUp(self):
        # We need to mock dependencies of MotionAnalyzer.__init__
        # to avoid complex setup or errors during initialization
        patcher_video_proc = patch('app.pipeline.analyzer.VideoProcessor')
        patcher_pose_ext = patch('app.pipeline.analyzer.PoseExtractor')
        patcher_norm = patch('app.pipeline.analyzer.PoseNormalizer')
        patcher_dtw = patch('app.pipeline.analyzer.DTWAligner')
        patcher_sim = patch('app.pipeline.analyzer.SimilarityCalculator')
        patcher_expr = patch('app.pipeline.analyzer._get_expression_analyzer')

        self.mock_video_proc = patcher_video_proc.start()
        self.mock_pose_ext = patcher_pose_ext.start()
        self.mock_norm = patcher_norm.start()
        self.mock_dtw = patcher_dtw.start()
        self.mock_sim = patcher_sim.start()
        self.mock_expr = patcher_expr.start()

        self.addCleanup(patcher_video_proc.stop)
        self.addCleanup(patcher_pose_ext.stop)
        self.addCleanup(patcher_norm.stop)
        self.addCleanup(patcher_dtw.stop)
        self.addCleanup(patcher_sim.stop)
        self.addCleanup(patcher_expr.stop)

        self.analyzer = MotionAnalyzer()

    def test_detect_jumping_start_frame_value_error_regression(self):
        """
        Test that _detect_jumping_start_frame does NOT raise ValueError
        when specific keypoints (e.g., ankles) are not detected (None baseline).
        Wait for format specifier error fix validation.
        """
        # Create a dummy sequence (T=10, 17, 3)
        # COCO Keypoints relevant:
        # 11=L_Hip, 12=R_Hip, 15=L_Ankle, 16=R_Ankle
        
        sequence = np.zeros((10, 17, 3))
        
        # Set only Hip keypoints as valid (detected)
        # Ankle keypoints remain 0 (not detected, score < 0.3)
        # Index 2 is score/confidence
        
        # Valid hip keypoints
        sequence[:, 11, 2] = 0.9  # L_Hip
        sequence[:, 12, 2] = 0.9  # R_Hip
        sequence[:, 11, 1] = 0.5  # Y pos
        sequence[:, 12, 1] = 0.5  # Y pos
        
        # Ankle keypoints are effectively 0 (score=0, y=0)
        # This will result in baseline_ankle_y being None
        
        try:
            # This call caused ValueError before the fix
            result = self.analyzer._detect_jumping_start_frame(sequence)
            
            # Should reach here without error
            self.assertEqual(result, ACTION_NOT_DETECTED, 
                             "Should return ACTION_NOT_DETECTED for partial data")
                             
        except ValueError as e:
            self.fail(f"Regression detected! ValueError raised: {e}")
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")

if __name__ == '__main__':
    unittest.main()
