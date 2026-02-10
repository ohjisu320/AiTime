import contextlib
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone

import pika
import requests

from app.config import get_settings
from app.pipeline.orchestrator import SpeechImitationPipelineOrchestrator

logger = logging.getLogger(__name__)


class SpeechImitationWorker:
    """RabbitMQ Worker for Speech Imitation Analysis"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.connection = None
        self.channel = None
        self.orchestrator = SpeechImitationPipelineOrchestrator()

    def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        parameters = pika.URLParameters(self.settings.RABBITMQ_URL)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # Declare queues
        self.channel.queue_declare(queue=self.settings.INPUT_QUEUE, durable=True)
        self.channel.queue_declare(queue=self.settings.OUTPUT_QUEUE, durable=True)

        logger.info(
            "Connected to RabbitMQ. Input Queue: %s, Output Queue: %s",
            self.settings.INPUT_QUEUE,
            self.settings.OUTPUT_QUEUE,
        )

    def publish_result(self, result: dict) -> None:
        """Publish analysis result to the output queue"""
        self.channel.basic_publish(
            exchange="",
            routing_key=self.settings.OUTPUT_QUEUE,
            body=json.dumps(result, ensure_ascii=False),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type="application/json",
            ),
        )

    def _publish_retry(
        self,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
        current_retry_count: int,
    ) -> None:
        """
        Publish the message again to the tail of the queue with incremented retry count
        """
        new_retry_count = current_retry_count + 1

        # properties.headers가 None일 수 있으므로 처리
        headers = properties.headers or {}
        headers["x-retry-count"] = new_retry_count

        new_props = pika.BasicProperties(
            delivery_mode=properties.delivery_mode,
            content_type=properties.content_type,
            headers=headers,
        )

        # 같은 큐로 다시 발행
        channel.basic_publish(
            exchange="",
            routing_key=self.settings.INPUT_QUEUE,
            body=body,
            properties=new_props,
        )
        logger.warning(
            f"Retrying message (count: {new_retry_count}/{self.settings.MAX_RETRIES})"
        )

    def _load_video_from_s3(self, s3_uri: str) -> str:
        """Download video from Presigned URL (requests)"""
        # s3_uri가 실제로는 presigned http(s) url이라고 가정
        try:
            response = requests.get(s3_uri, stream=True, timeout=60)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                return tmp.name
        except Exception as e:
            raise ValueError(f"Failed to download video from {s3_uri}: {e}") from e

    def _calculate_freq_abnormal(self, rep_data: dict) -> bool:
        """
        Calculate freq_abnormal based on squeal ratio or abnormal pitch (MAD).
        Logic: squeal_ratio > 0 OR mad_semitone out of normal range
        (1.0 ~ 2.0?? -> config dependent)
        Actually user said: 'squeal exists OR pitch abnormal'

        We use internal thresholds from settings if available, or just check values.
        Using settings for consistency.
        """
        squeal = rep_data.get("child_squeal_ratio")
        mad = rep_data.get("child_mad_semitone")

        # 1. Squeal check
        is_squeal = squeal is not None and squeal > 0

        # 2. Pitch Abnormal check (Monotone or Song/Exaggerated)
        # Normal range is typically between monotone and song threshold?
        # Actually config definitions:
        # PITCH_MAD_MONOTONE_THRESHOLD = 1.0
        # PITCH_MAD_SONG_THRESHOLD = 2.0
        # Usually 'abnormal' means too flat (monotone) or too wild?
        # Let's assume 'abnormal' implies pathology, often Monotone in ASD.
        # But 'Song' quality is often good.
        # However, user said "abnormal pitch". Let's assume Monotone (MAD < Threshold).
        # OR let's treat anything outside "Normal" as abnormal?
        # User defined: "freq_abnormal matches if squeal OR abnormal pitch"
        # Let's interpret "abnormal pitch" as "Monotone" (< 1.0)
        # for now as that's the negative indicator for ASD.

        is_abnormal_pitch = False
        if mad is not None and mad < self.settings.PITCH_MAD_MONOTONE_THRESHOLD:
            is_abnormal_pitch = True

        return is_squeal or is_abnormal_pitch

    def _save_benchmark_metrics(self, internal_result: dict) -> None:
        """
        Save processing times and metric distributions to a local JSONL file.
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            log_dir = os.path.join("artifacts", "benchmarks")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(
                log_dir, f"{timestamp}_speech_imitation_latency.jsonl"
            )

            processing_times = internal_result.get("processing_times", {})
            metrics = internal_result.get("metrics", {})
            per_trial = metrics.get("per_trial", [])

            # Flatten metrics for distribution analysis
            latencies = []
            pitch_values = []
            mad_values = []

            for t in per_trial:
                for r in t.get("repetitions", []):
                    if r.get("latency_s") is not None:
                        latencies.append(r["latency_s"])
                    if r.get("child_mean_f0") is not None:
                        pitch_values.append(r["child_mean_f0"])
                    if r.get("child_mad_semitone") is not None:
                        mad_values.append(r["child_mad_semitone"])

            log_entry = {
                "run_id": internal_result.get("request_id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_times": processing_times,
                "metrics_distribution": {
                    "latency_s": latencies,
                    "child_mean_f0": pitch_values,
                    "child_mad_semitone": mad_values,
                },
            }

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"Failed to save benchmark metrics: {e}")

    def process_message(
        self,
        ch: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Callback for processing received messages"""
        start_time = time.time()

        # Retry Header Check
        headers = properties.headers or {}
        retry_count = headers.get("x-retry-count", 0)

        # 1. Payload Parsing
        try:
            task = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Failed to decode message body: %s", body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Required fields
        # {
        #   "examId": "UUID",
        #   "videoId":  "UUID",
        #   "videoType": "POSE_IMITATION" | "SPEECH_IMITATION" | ...
        #   "childName": "아무개",
        #   "ageMonths": 18,
        #    "s3Uri": "s3://your-bucket/..." (Presigned URL)
        # }

        exam_id = task.get("examId")
        video_id = task.get("videoId")
        video_type = task.get("videoType")
        age_months = task.get("ageMonths")
        s3_uri = task.get("s3Uri")

        # Validation
        if not all([exam_id, video_id, age_months, s3_uri]):
            logger.error("Missing required fields in task: %s", task)
            # Cannot process, discard or publish error?
            # If critical fields missing, fail immediately.
            self._publish_failure(task, "Missing required fields", start_time)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(
            "Received task: examId=%s, videoId=%s, age=%s",
            exam_id,
            video_id,
            age_months,
        )

        tmp_path = None
        try:
            # 2. Download Video
            tmp_path = self._load_video_from_s3(s3_uri)

            # 3. Run Analysis
            # orchestrator returns internal dict format
            internal_result = self.orchestrator.run(
                video_path=tmp_path, age_months=int(age_months), request_id=exam_id
            )

            # 4. Map Results
            internal_metrics = internal_result.get("metrics", {})
            internal_per_trial = internal_metrics.get("per_trial", [])
            internal_ados = internal_metrics.get("ADOS", {})

            # Map per_trial
            output_per_trial = []
            for t in internal_per_trial:
                reps = t.get("repetitions", [])
                if not reps:
                    continue
                # Use 1st rep as trial result (assuming 1 rep per trial)
                r = reps[0]

                # Check metrics availability
                # start/end times currently might be None in internal result
                # if not populated.
                # internal result 'stimulus_time' is tuple (start, end)
                stim_time = r.get("stimulus_time")
                trial_start = stim_time[0] if stim_time else 0.002  # Fallback/Default
                trial_end = stim_time[1] if stim_time else 0.67

                freq_abnormal = self._calculate_freq_abnormal(r)

                output_per_trial.append(
                    {
                        "trial_index": t.get("trial_index"),
                        "trial_start_s": trial_start,
                        "trial_end_s": trial_end,
                        "stimulus_id": t.get("stimulus_id"),
                        "stimulus_text": t.get("stimulus_text"),
                        "response_detected": r.get("response_detected", False),
                        "latency_s": r.get("latency_s"),
                        "success": r.get("success", False),
                        "failure_reason": r.get("failure_reason"),
                        "freq_abnormal": freq_abnormal,
                    }
                )

            # Map ADOS
            # Internal: A3 (0~3), B18 (True/False)
            output_ados = {
                "A3": internal_ados.get("A3", 0),
                "B18": internal_ados.get("B18", False),
            }

            # Final Output Construct
            final_output = {
                "examId": exam_id,
                "videoId": video_id,
                "videoType": video_type,
                "analyzedAt": datetime.now(timezone.utc).astimezone().isoformat(),
                "status": "SUCCESS",
                "metrics": {"per_trial": output_per_trial},
                "ADOS": output_ados,
            }

            # 5. Publish Success
            self._save_benchmark_metrics(internal_result)
            self.publish_result(final_output)
            logger.info("Task %s (examId) completed successfully.", exam_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.exception("Task failed: %s", e)

            # Retry Logic
            if retry_count < self.settings.MAX_RETRIES:
                # Cleanup before retry
                if tmp_path and os.path.exists(tmp_path):
                    with contextlib.suppress(Exception):
                        os.remove(tmp_path)

                self._publish_retry(ch, method, properties, body, retry_count)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # Max retries reached -> Fail
                self._publish_failure(task, str(e), start_time, status="FAILED")
                ch.basic_ack(delivery_tag=method.delivery_tag)

        finally:
            # Cleanup temp file
            if tmp_path and os.path.exists(tmp_path):
                with contextlib.suppress(Exception):
                    os.remove(tmp_path)

    def _publish_failure(
        self, task: dict, error_msg: str, start_time: float, status: str = "FAILED"
    ) -> None:
        """Publish failure message matching the schema as best as possible"""
        final_output = {
            "examId": task.get("examId"),
            "videoId": task.get("videoId"),
            "videoType": task.get("videoType"),
            "analyzedAt": datetime.now(timezone.utc).astimezone().isoformat(),
            "status": status,
            "metrics": {"per_trial": []},
            "ADOS": {"A3": 0, "B18": False},
        }
        self.publish_result(final_output)

    def start(self) -> None:
        """Start the worker"""
        self.connect()
        # QoS: Process 1 message at a time
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.settings.INPUT_QUEUE, on_message_callback=self.process_message
        )

        logger.info(
            "Worker started. Waiting for messages in '%s'...", self.settings.INPUT_QUEUE
        )
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Worker stopping...")
            self.channel.stop_consuming()
        finally:
            if self.connection:
                self.connection.close()


if __name__ == "__main__":
    # Ensure logging is configured if run directly
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    worker = SpeechImitationWorker()
    worker.start()
