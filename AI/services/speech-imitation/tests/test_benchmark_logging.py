import json
import os
import unittest
from unittest.mock import MagicMock, mock_open, patch

from app.worker import SpeechImitationWorker


class TestBenchmarkLogging(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = SpeechImitationWorker()
        # Suppress logging during tests
        self.worker.logger = MagicMock()

    @patch("app.worker.open", new_callable=mock_open)
    @patch("app.worker.os.makedirs")
    @patch("app.worker.datetime")
    def test_save_benchmark_metrics_success(
        self, mock_datetime: MagicMock, mock_makedirs: MagicMock, mock_file: MagicMock
    ) -> None:
        # 1. Setup Mock Data
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01"
        # Need to handle datetime.now(timezone.utc).isoformat() call
        # inside the valid logic
        # mocking the whole datetime class can be tricky if not careful with attributes.
        # But let's assume simple mocking works for strftime and now().isoformat()

        # We need to mock datetime.now(timezone.utc).isoformat()
        # The code calls: datetime.now(timezone.utc).isoformat()
        # So mock_datetime.now.return_value.isoformat.return_value
        # = "2023-01-01T00:00:00+00:00"
        # AND mock_datetime.now.return_value.strftime.return_value
        # = "2023-01-01"
        # However, datetime.now called with args vs without args
        # might return same mock object standardly.
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01"
        mock_datetime.now.return_value.isoformat.return_value = "SO-ISO-FORMAT"

        internal_result = {
            "request_id": "test_run_123",
            "processing_times": {"vad": 0.1, "pitch": 0.5},
            "metrics": {
                "per_trial": [
                    {
                        "repetitions": [
                            {
                                "latency_s": 0.2,
                                "child_mean_f0": 300.5,
                                "child_mad_semitone": 1.2,
                            },
                            {
                                # Should be skipped or handled? Code skips None check
                                "latency_s": None,
                                "child_mean_f0": None,
                            },
                            {
                                "latency_s": 0.4,
                                "child_mean_f0": 305.0,
                                "child_mad_semitone": 1.1,
                            },
                        ]
                    }
                ]
            },
        }

        # 2. Execution
        self.worker._save_benchmark_metrics(internal_result)

        # 3. Verification

        # Directories are created?
        mock_makedirs.assert_called_with(
            os.path.join("artifacts", "benchmarks"), exist_ok=True
        )

        # File opened?
        # filename depends on mocked date:
        # "artifacts/benchmarks/2023-01-01_speech_imitation_latency.jsonl"
        # Use os.path.join to match platform separator
        expected_path = os.path.join(
            "artifacts", "benchmarks", "2023-01-01_speech_imitation_latency.jsonl"
        )
        mock_file.assert_called_with(expected_path, "a", encoding="utf-8")

        # Written content?
        handle = mock_file()
        handle.write.assert_called_once()
        args, _ = handle.write.call_args
        written_str = args[0]

        # Parse JSON
        # The content should be json_string + "\n"
        self.assertTrue(written_str.endswith("\n"))
        log_entry = json.loads(written_str.strip())

        self.assertEqual(log_entry["run_id"], "test_run_123")
        self.assertEqual(log_entry["processing_times"], {"vad": 0.1, "pitch": 0.5})

        # Metrics distribution check
        dist = log_entry.get("metrics_distribution", {})
        self.assertEqual(dist["latency_s"], [0.2, 0.4])
        self.assertEqual(dist["child_mean_f0"], [300.5, 305.0])
        self.assertEqual(dist["child_mad_semitone"], [1.2, 1.1])


if __name__ == "__main__":
    unittest.main()
