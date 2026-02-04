import base64
import contextlib
import datetime
import json
import logging
import os
import tempfile

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
        try:
            task = json.loads(body)
        except json.JSONDecodeError:
            logger.error("잘못된 JSON 형식 수신: %s", body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # extract identifiers for logging
        exam_id = task.get("examId", "unknown")
        video_id = task.get("videoId", "unknown")
        logger.info("작업 수신: examId=%s videoId=%s", exam_id, video_id)

        tmp_path = None
        analyzed_at = datetime.datetime.now().astimezone().isoformat()

        try:
            # 비디오 로드 (S3 Presigned URL 지원)
            video_path = self._load_video(task)
            # 다운로드된 임시 파일인 경우 나중에 삭제하기 위해 경로 저장
            if video_path != task.get("video_path"):
                tmp_path = video_path

            # 분석 실행
            result = self.engine.analyzer.analyze(video_path)

            # 결과 매핑 (내부 포맷 -> 요구사항 포맷)
            output_message = self._format_success_result(task, result, analyzed_at)

            logger.info(
                "작업 성공: examId=%s success=%s/%s",
                exam_id,
                result.get("summary", {}).get("success_count"),
                result.get("summary", {}).get("total_call_count"),
            )

        except Exception as e:
            logger.exception("작업 실패: examId=%s", exam_id)
            output_message = self._format_error_result(task, str(e), analyzed_at)

        finally:
            # 임시 파일 정리
            if tmp_path and os.path.exists(tmp_path):
                with contextlib.suppress(Exception):
                    os.remove(tmp_path)

        self.publish_result(output_message)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _load_video(self, task: dict) -> str:
        """비디오 로드 (s3Uri, video_path 등)"""
        # 1. 로컬 경로 (개발/텍스트용)
        if "video_path" in task:
            path = task["video_path"]
            if not os.path.exists(path):
                raise ValueError(f"비디오 경로를 찾을 수 없음: {path}")
            return path

        # 2. S3 URI (Presigned URL) 또는 일반 URL
        s3_uri = task.get("s3Uri")
        if s3_uri:
            # URL이 http로 시작하면 다운로드 (Presigned URL 포함)
            if s3_uri.startswith("http"):
                logger.info("비디오 다운로드 시작: %s", s3_uri)
                response = requests.get(s3_uri, timeout=60, stream=True)
                response.raise_for_status()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    return tmp.name

            # (혹시나) 로컬 경로로 들어온 경우
            if os.path.exists(s3_uri):
                return s3_uri

        # 3. Base64 (레거시 지원)
        if "video_base64" in task:
            video_data = base64.b64decode(task["video_base64"])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_data)
                return tmp.name

        raise ValueError("유효한 비디오 소스가 없습니다 (s3Uri 또는 video_path 필요)")

    def _format_success_result(
        self, task: dict, result: dict, analyzed_at: str
    ) -> dict:
        """분석 성공 시 결과 포맷팅"""

        # metrics.per_trial 매핑
        per_trial = []
        for call in result.get("per_call", []):
            per_trial.append(
                {
                    "trial_index": call["call_index"],
                    "trial_start_s": call["call_start_s"],
                    "trial_end_s": call["call_end_s"],
                    "success": call["success"],
                    "latency_s": call["latency_s"],
                    "gaze_duration_s": call["gaze_duration_s"],
                    "emotion": call["dominant_emotion"],  # null or str
                }
            )

        return {
            "examId": task.get("examId"),
            "videoId": task.get("videoId"),
            "videoType": "NAME_FACING",
            "childName": task.get("childName"),
            "ageMonths": task.get("ageMonths"),
            "analyzedAt": analyzed_at,
            "status": "SUCCESS",
            "metrics": {"per_trial": per_trial},
            "ADOS": result.get("ADOS", {}),
        }

    def _format_error_result(
        self, task: dict, error_msg: str, analyzed_at: str
    ) -> dict:
        """분석 실패 시 결과 포맷팅"""
        return {
            "examId": task.get("examId"),
            "videoId": task.get("videoId"),
            "videoType": "NAME_FACING",
            "childName": task.get("childName"),
            "ageMonths": task.get("ageMonths"),
            "analyzedAt": analyzed_at,
            "status": "FAILED",
            "error": error_msg,
            "metrics": {"per_trial": []},
            "ADOS": {
                "B1": 0,
                "B4": 0,
                "B6": False,
                "B18": False,
            },  # 실패 시 기본값 (또는 null 처리 정책에 따라 변경 가능)
        }

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
