import base64
import contextlib
import json
import logging
import os
import tempfile
import time

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

    def _load_video(self, task: dict) -> str:
        """Load video from task payload (path, url, or base64)"""
        if "video_path" in task:
            path = task["video_path"]
            if not os.path.exists(path):
                raise ValueError(f"Video path not found: {path}")
            return path

        if "video_url" in task:
            response = requests.get(task["video_url"], timeout=60)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(response.content)
                return tmp.name

        if "video_base64" in task:
            video_data = base64.b64decode(task["video_base64"])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_data)
                return tmp.name

        raise ValueError(
            "No video source provided (video_path, video_url, or video_base64)"
        )

    def process_message(
        self,
        ch: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        _properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Callback for processing received messages"""
        start_time = time.time()
        try:
            task = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Failed to decode message body: %s", body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        task_id = task.get("task_id", "unknown")
        age_months = task.get("age_months")
        if age_months is None:
            logger.error("Missing 'age_months' in task %s", task_id)
            # Depending on policy, might want to ack and discard, or publish error.
            # Here we publish an error result.
            self._publish_error(task_id, "Missing 'age_months'", task.get("metadata"))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info("Received task: %s (age: %s)", task_id, age_months)

        tmp_path = None
        try:
            # 1. Load Video
            video_path = self._load_video(task)
            # If we created a temp file, mark it for deletion
            if video_path != task.get("video_path"):
                tmp_path = video_path

            # 2. Run Analysis
            # orchestrator.run returns a dict result
            result_data = self.orchestrator.run(
                video_path=video_path, age_months=int(age_months), request_id=task_id
            )

            # 3. Construct Result Message
            result_message = {
                "task_id": task_id,
                "status": "success",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "result": result_data,
                "metadata": task.get("metadata"),
            }

            logger.info("Task %s completed successfully.", task_id)

        except Exception as e:
            logger.exception("Task %s failed: %s", task_id, e)
            result_message = {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "metadata": task.get("metadata"),
            }

        finally:
            # Cleanup temp file
            if tmp_path and os.path.exists(tmp_path):
                with contextlib.suppress(Exception):
                    os.remove(tmp_path)

        # 4. Publish Result
        self.publish_result(result_message)

        # 5. Acknowledge Message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _publish_error(self, task_id: str, error_msg: str, metadata: dict) -> None:
        result_message = {
            "task_id": task_id,
            "status": "failed",
            "error": error_msg,
            "metadata": metadata,
        }
        self.publish_result(result_message)

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
