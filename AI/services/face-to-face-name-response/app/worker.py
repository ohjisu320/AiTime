import base64
import contextlib
import json
import logging
import os
import tempfile
import time

import pika
import requests

from app.rtn.config import RabbitMQConfig
from app.rtn.service.engine import build_engine

logger = logging.getLogger(__name__)


class FaceNameWorker:
    """RabbitMQ 메시지 컨슈머 - 얼굴 대면 이름 반응 분석"""

    def __init__(self, config: RabbitMQConfig | None = None) -> None:
        self.config = config or RabbitMQConfig()
        self.connection = None
        self.channel = None

        # 엔진/분석기 초기화
        self.engine, _ = build_engine(enable_mjpeg=False, debug=False)

    def connect(self) -> None:
        """RabbitMQ 연결"""
        credentials = pika.PlainCredentials(self.config.user, self.config.password)
        parameters = pika.ConnectionParameters(
            host=self.config.host, port=self.config.port, credentials=credentials
        )

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # 큐 선언
        self.channel.queue_declare(queue=self.config.task_queue, durable=True)
        self.channel.queue_declare(queue=self.config.result_queue, durable=True)

        logger.info("RabbitMQ에 연결됨: %s:%s", self.config.host, self.config.port)

    def publish_result(self, result: dict) -> None:
        """결과를 Result Queue로 발행"""
        self.channel.basic_publish(
            exchange="",
            routing_key=self.config.result_queue,
            body=json.dumps(result, ensure_ascii=False),
            properties=pika.BasicProperties(
                delivery_mode=2,  # 메시지 영속성
                content_type="application/json",
            ),
        )

    def process_message(
        self,
        ch: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        _properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """메시지 처리 콜백"""
        start_time = time.time()
        task = json.loads(body)

        task_id = task.get("task_id", "unknown")
        logger.info("작업 수신: %s", task_id)

        tmp_path = None

        try:
            # 비디오 로드
            video_path = self._load_video(task)
            tmp_path = video_path if video_path != task.get("video_path") else None

            # 분석 실행
            result = self.engine.analyzer.analyze(video_path)

            # 결과 발행
            result_message = {
                "task_id": task_id,
                "status": "success",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "result": result,
                "metadata": task.get("metadata"),
            }

            summary = result.get("summary", {}) if isinstance(result, dict) else {}
            logger.info(
                "작업 %s 완료: success=%s/%s",
                task_id,
                summary.get("success_count"),
                summary.get("total_call_count"),
            )

        except Exception:
            result_message = {
                "task_id": task_id,
                "status": "failed",
                "error": str(Exception),
                "metadata": task.get("metadata"),
            }
            logger.exception("작업 %s 실패", task_id)

        finally:
            # 임시 파일 정리
            if tmp_path and os.path.exists(tmp_path):
                with contextlib.suppress(Exception):
                    os.remove(tmp_path)

        self.publish_result(result_message)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _load_video(self, task: dict) -> str:
        """비디오 로드 (로컬 경로, URL, 또는 Base64)"""
        if "video_path" in task:
            path = task["video_path"]
            if not os.path.exists(path):
                raise ValueError(f"비디오 경로를 찾을 수 없음: {path}")
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
            "비디오 소스가 제공되지 않음 "
            "(video_path, video_url, 또는 video_base64 중 하나 필요)"
        )

    def start(self) -> None:
        """워커 시작"""
        self.connect()

        # prefetch_count=1: 한 번에 하나씩 처리
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.config.task_queue, on_message_callback=self.process_message
        )

        logger.info("워커 시작됨. '%s' 큐에서 작업 대기 중...", self.config.task_queue)
        logger.info("종료하려면 CTRL+C를 누르세요")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("워커 종료 중...")
            self.channel.stop_consuming()
        finally:
            if self.connection:
                self.connection.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    worker = FaceNameWorker()
    worker.start()
