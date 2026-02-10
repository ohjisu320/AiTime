import json
import unittest
from unittest.mock import MagicMock, patch

from app.worker import SpeechImitationWorker


class TestSpeechImitationWorker(unittest.TestCase):
    def setUp(self) -> None:
        # Mock settings
        self.patcher_settings = patch("app.worker.get_settings")
        self.mock_settings = self.patcher_settings.start()
        self.mock_settings.return_value.RABBITMQ_URL = (
            "amqp://guest:guest@localhost:5672/"
        )
        self.mock_settings.return_value.INPUT_QUEUE = "input_queue"
        self.mock_settings.return_value.OUTPUT_QUEUE = "output_queue"
        self.mock_settings.return_value.MAX_RETRIES = 3
        self.mock_settings.return_value.PITCH_MAD_MONOTONE_THRESHOLD = 1.0

        # Create worker
        self.worker = SpeechImitationWorker()
        self.worker.connection = MagicMock()
        self.worker.channel = MagicMock()

        # Mock orchestrator
        self.worker.orchestrator = MagicMock()

    def tearDown(self) -> None:
        self.patcher_settings.stop()

    @patch("app.worker.requests.get")
    @patch("app.worker.tempfile.NamedTemporaryFile")
    @patch("app.worker.os.remove")
    @patch("app.worker.os.path.exists")
    def test_process_message_success(
        self,
        mock_exists: MagicMock,
        mock_remove: MagicMock,
        mock_temp: MagicMock,
        mock_requests: MagicMock,
    ) -> None:
        # Setup mocks
        mock_exists.return_value = True
        mock_temp.return_value.__enter__.return_value.name = "/tmp/fake_video.mp4"

        # Requests mock
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_requests.return_value = mock_resp

        # Orchestrator mock
        self.worker.orchestrator.run.return_value = {
            "metrics": {
                "per_trial": [
                    {
                        "trial_index": 1,
                        "stimulus_id": "S1",
                        "stimulus_text": "text",
                        "repetitions": [
                            {
                                "response_detected": True,
                                "latency_s": 0.5,
                                "success": True,
                                "child_squeal_ratio": 0.0,
                                "child_mad_semitone": 1.5,  # Normal
                                "stimulus_time": (0.1, 0.5),
                            }
                        ],
                    }
                ],
                "ADOS": {"A3": 1, "B18": True},
            }
        }

        # Input message
        body = json.dumps(
            {
                "examId": "exam123",
                "videoId": "vid123",
                "videoType": "SPEECH_IMITATION",
                "childName": "Child",
                "ageMonths": 18,
                "s3Uri": "https://fake-s3-url.com/vid.mp4",
            }
        ).encode("utf-8")

        method = MagicMock()
        props = MagicMock()
        props.headers = {}

        # Run
        self.worker.process_message(self.worker.channel, method, props, body)

        # Verify
        # 1. Download called
        mock_requests.assert_called_with(
            "https://fake-s3-url.com/vid.mp4", stream=True, timeout=60
        )

        # 2. Orchestrator called
        self.worker.orchestrator.run.assert_called()

        # 3. Publish result
        self.worker.channel.basic_publish.assert_called_once()
        args, kwargs = self.worker.channel.basic_publish.call_args
        published_body = json.loads(kwargs["body"])

        self.assertEqual(published_body["status"], "SUCCESS")
        self.assertEqual(published_body["examId"], "exam123")
        self.assertEqual(len(published_body["metrics"]["per_trial"]), 1)
        self.assertFalse(
            published_body["metrics"]["per_trial"][0]["freq_abnormal"]
        )  # 1.5 > 1.0 (Normal)

        # 4. Ack
        self.worker.channel.basic_ack.assert_called_with(
            delivery_tag=method.delivery_tag
        )

    @patch("app.worker.requests.get")
    def test_retry_logic(self, mock_requests: MagicMock) -> None:
        # Simulate download failure
        mock_requests.side_effect = Exception("Download failed")

        body = json.dumps(
            {
                "examId": "exam_fail",
                "videoId": "v",
                "videoType": "T",
                "childName": "C",
                "ageMonths": 18,
                "s3Uri": "bad_url",
            }
        ).encode("utf-8")

        method = MagicMock()
        props = MagicMock()
        props.headers = {}  # First attempt
        props.delivery_mode = 2
        props.content_type = "application/json"

        self.worker.process_message(self.worker.channel, method, props, body)

        # Expect retry publish
        self.worker.channel.basic_publish.assert_called()
        args, kwargs = self.worker.channel.basic_publish.call_args

        # Check if sent to input queue (for retry)
        self.assertEqual(kwargs["routing_key"], "input_queue")
        self.assertEqual(kwargs["properties"].headers["x-retry-count"], 1)

        # Check ack of original
        self.worker.channel.basic_ack.assert_called()

    @patch("app.worker.requests.get")
    def test_max_retries_fail(self, mock_requests: MagicMock) -> None:
        # Simulate failure
        mock_requests.side_effect = Exception("Persistent failure")

        body = json.dumps(
            {
                "examId": "exam_max_fail",
                "videoId": "v",
                "videoType": "T",
                "childName": "C",
                "ageMonths": 18,
                "s3Uri": "u",
            }
        ).encode("utf-8")

        method = MagicMock()
        props = MagicMock()
        # Max retries reached
        # (already retried 3 times, so count is 3.
        # logic: count < MAX(3). 3 < 3 is False -> Fail)
        props.headers = {"x-retry-count": 3}

        self.worker.process_message(self.worker.channel, method, props, body)

        # Expect FAIL result publish
        self.worker.channel.basic_publish.assert_called()
        args, kwargs = self.worker.channel.basic_publish.call_args

        # Sent to output queue
        self.assertEqual(kwargs["routing_key"], "output_queue")
        published_body = json.loads(kwargs["body"])
        self.assertEqual(published_body["status"], "FAILED")

        # Ack original
        self.worker.channel.basic_ack.assert_called()

    def test_freq_abnormal_logic(self) -> None:
        # Test 1: Squeal
        res = self.worker._calculate_freq_abnormal({"child_squeal_ratio": 0.5})
        self.assertTrue(res)

        # Test 2: Monotone (MAD < 1.0)
        res = self.worker._calculate_freq_abnormal(
            {"child_squeal_ratio": 0.0, "child_mad_semitone": 0.5}
        )
        self.assertTrue(res)

        # Test 3: Normal
        res = self.worker._calculate_freq_abnormal(
            {"child_squeal_ratio": 0.0, "child_mad_semitone": 1.5}
        )
        self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
