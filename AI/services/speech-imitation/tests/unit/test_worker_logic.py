import json
import unittest
from unittest.mock import MagicMock, patch

from app.worker import SpeechImitationWorker


class TestSpeechImitationWorker(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_channel = MagicMock()
        self.mock_method = MagicMock()
        self.mock_properties = MagicMock()
        self.worker = SpeechImitationWorker()
        self.worker.channel = self.mock_channel
        self.worker.settings = (
            MagicMock()
        )  # Mock settings so we don't need real RabbitMQ config
        self.worker.settings.INPUT_QUEUE = "test_input"
        self.worker.settings.OUTPUT_QUEUE = "test_output"

        # Mock the orchestrator to avoid running actual heavy AI models
        self.worker.orchestrator = MagicMock()
        self.worker.orchestrator.run.return_value = {"mock_result": "success"}

    @patch("os.path.exists")
    def test_process_message_success(self, mock_exists: MagicMock) -> None:
        # Scenario: Message with video_path
        message = {
            "task_id": "test_123",
            "age_months": 18,
            "video_path": "/tmp/test.mp4",
            "metadata": {"user": "test"},
        }
        body = json.dumps(message).encode("utf-8")
        mock_exists.return_value = True  # Video exists

        self.worker.process_message(
            self.mock_channel, self.mock_method, self.mock_properties, body
        )

        # Verify Orchestrator called
        self.worker.orchestrator.run.assert_called_once_with(
            video_path="/tmp/test.mp4", age_months=18, request_id="test_123"
        )

        # Verify Result Published
        self.mock_channel.basic_publish.assert_called_once()
        args, kwargs = self.mock_channel.basic_publish.call_args
        published_body = json.loads(kwargs["body"])

        self.assertEqual(published_body["task_id"], "test_123")
        self.assertEqual(published_body["status"], "success")
        self.assertEqual(published_body["result"], {"mock_result": "success"})

        # Verify Ack
        self.mock_channel.basic_ack.assert_called_once()

    def test_process_message_missing_age(self) -> None:
        # Scenario: Message missing age_months
        message = {"task_id": "test_error", "video_path": "/tmp/test.mp4"}
        body = json.dumps(message).encode("utf-8")

        self.worker.process_message(
            self.mock_channel, self.mock_method, self.mock_properties, body
        )

        # Verify Orchestrator NOT called
        self.worker.orchestrator.run.assert_not_called()

        # Verify Error Published
        self.mock_channel.basic_publish.assert_called_once()
        args, kwargs = self.mock_channel.basic_publish.call_args
        published_body = json.loads(kwargs["body"])

        self.assertEqual(published_body["status"], "failed")
        self.assertIn("Missing 'age_months'", published_body["error"])

        # Verify Ack
        self.mock_channel.basic_ack.assert_called_once()


if __name__ == "__main__":
    unittest.main()
