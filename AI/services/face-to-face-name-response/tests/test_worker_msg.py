import json
import logging
import unittest
from unittest.mock import MagicMock, patch

from app.worker import FaceNameWorker


class TestFaceNameWorkerMsg(unittest.TestCase):
    def setUp(self) -> None:
        # Mock Engine & Analyzer
        self.mock_engine = MagicMock()
        self.mock_analyzer = MagicMock()
        self.mock_engine.analyzer = self.mock_analyzer

        # Patch build_engine to return our mock
        patcher = patch(
            "app.worker.build_engine", return_value=(self.mock_engine, None)
        )
        self.mock_build_engine = patcher.start()
        self.addCleanup(patcher.stop)

        self.worker = FaceNameWorker()

        # Mock Connection & Channel
        self.worker.connection = MagicMock()
        self.worker.channel = MagicMock()

    def test_process_message_success(self) -> None:
        # Input Task
        task_input = {
            "examId": "test-exam-id",
            "videoId": "test-video-id",
            "videoType": "NAME_FACING",
            "childName": "TestChild",
            "ageMonths": 18,
            "s3Uri": "http://example.com/video.mp4",
        }
        body = json.dumps(task_input).encode("utf-8")

        # Mock Analyzer Result
        mock_result = {
            "summary": {"success_count": 1, "total_call_count": 2},
            "per_call": [
                {
                    "call_index": 1,
                    "call_start_s": 1.0,
                    "call_end_s": 2.0,
                    "success": False,
                    "latency_s": None,
                    "gaze_duration_s": 0.0,
                    "dominant_emotion": "Neutral",
                },
                {
                    "call_index": 2,
                    "call_start_s": 5.0,
                    "call_end_s": 6.0,
                    "success": True,
                    "latency_s": 0.5,
                    "gaze_duration_s": 2.0,
                    "dominant_emotion": "Happiness",
                },
            ],
            "ADOS": {"B1": 1, "B4": 1, "B6": True, "B18": True},
        }
        self.mock_analyzer.analyze.return_value = mock_result

        # Mock Requests (Video Download)
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"video_chunk"]
            mock_get.return_value = mock_response

            # Execute
            self.worker.process_message(
                self.worker.channel, MagicMock(), MagicMock(), body
            )

            # Verify Download
            mock_get.assert_called_with(
                "http://example.com/video.mp4", timeout=60, stream=True
            )

            # Verify Output
            call_args = self.worker.channel.basic_publish.call_args
            output_body = json.loads(call_args.kwargs["body"])

            print(json.dumps(output_body, indent=2, ensure_ascii=False))

            self.assertEqual(output_body["examId"], "test-exam-id")
            self.assertEqual(output_body["status"], "SUCCESS")
            self.assertEqual(
                output_body["metrics"]["per_trial"][1]["emotion"], "Happiness"
            )
            self.assertEqual(output_body["ADOS"]["B6"], True)

    def test_process_message_failed(self) -> None:
        # Input Task
        task_input = {"examId": "fail-exam-id", "s3Uri": "http://example.com/fail.mp4"}
        body = json.dumps(task_input).encode("utf-8")

        # Mock Exception
        self.mock_analyzer.analyze.side_effect = RuntimeError("Analysis Error")

        # Mock Requests
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"video"]
            mock_get.return_value = mock_response

            # Execute
            self.worker.process_message(
                self.worker.channel, MagicMock(), MagicMock(), body
            )

            # Verify Output
            call_args = self.worker.channel.basic_publish.call_args
            output_body = json.loads(call_args.kwargs["body"])

            print(json.dumps(output_body, indent=2, ensure_ascii=False))

            self.assertEqual(output_body["status"], "FAILED")
            self.assertIn("Analysis Error", output_body["error"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
