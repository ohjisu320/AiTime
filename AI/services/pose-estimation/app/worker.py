# AI/services/pose-estimation/app/worker.py
"""RabbitMQ 컨슈머 (메시지 수신 및 처리)"""

import base64
import contextlib
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone, timedelta

import pika
import requests

from app.config import settings, RabbitMQConfig
from app.models.vitpose import get_model
from app.pipeline.analyzer import MotionAnalyzer, PoseImitationResponse

logger = logging.getLogger(__name__)

# ==================== 월령별 동작 세트 상수 ====================
ACTION_SET_12_17 = ["clapping", "hurray", "walking_back"]  # 12-17개월: 손뼉치기, 만세하기, 뒤로걷기
ACTION_SET_18_24 = ["jumping", "kicking", "throwing"]      # 18-24개월: 양발모아뛰기, 공차기, 공던지기


def get_action_set_by_age(age_months: int) -> list[str]:
    """
    월령에 따른 동작 세트 반환.
    
    Args:
        age_months: 아동 월령
        
    Returns:
        동작 리스트 (3개)
        
    Raises:
        ValueError: 지원하지 않는 월령 범위 (12-24개월만 지원)
    """
    if 12 <= age_months <= 17:
        return ACTION_SET_12_17.copy()
    elif 18 <= age_months <= 24:
        return ACTION_SET_18_24.copy()
    else:
        raise ValueError(f"지원하지 않는 월령: {age_months}. 12-24개월만 지원됩니다.")


class PoseWorker:
    """RabbitMQ 메시지 컨슈머 - 포즈 모방 분석"""
    
    def __init__(self, config: RabbitMQConfig | None = None) -> None:
        self.config = config or RabbitMQConfig()
        self.connection = None
        self.channel = None
        
        # 모델 및 분석기 초기화
        self.model = get_model()
        self.analyzer = MotionAnalyzer()
    
    def connect(self) -> None:
        """RabbitMQ 연결"""
        credentials = pika.PlainCredentials(self.config.user, self.config.password)
        parameters = pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            credentials=credentials
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
                content_type="application/json"
            )
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
        
        exam_id = task.get("exam_id", "unknown")
        logger.info("작업 수신: %s", exam_id)
        
        tmp_path = None
        
        try:
            # 비디오 로드
            video_path = self._load_video(task)
            tmp_path = video_path if video_path != task.get("video_path") else None
            
            # 분석 파라미터
            age_months = task["age_months"]
            name = task.get("name", "unknown")
            
            # 월령에 따른 동작 세트 자동 결정
            action_list = get_action_set_by_age(age_months)
            
            logger.info("pose_imitation 분석 시작: %s (%d개월)", name, age_months)
            logger.info("동작 세트: %s", action_list)
            
            # 분석 수행
            result = self.analyzer.analyze_multi_trial(
                video_path=video_path,
                action_list=action_list,
                age_months=age_months
            )
            
            # 결과 메시지 생성
            result_message = {
                "exam_id": exam_id,
                "video_type": "pose_imitation",
                "status": "success",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "result": {
                    "metrics": result.metrics,
                    "ados": result.ados
                },
                "metadata": task.get("metadata")
            }
            
            success_count = sum(1 for t in result.metrics["per_trial"] if t["success"])
            logger.info("작업 %s 완료: %d/3 성공", exam_id, success_count)
            logger.info("ADOS 결과: %s", result.ados)
            
        except KeyError as e:
            error_msg = f"필수 필드 누락: {e}"
            logger.error("%s: %s", exam_id, error_msg)
            result_message = {
                "exam_id": exam_id,
                "video_type": "pose_imitation",
                "status": "failed",
                "error": error_msg,
                "metadata": task.get("metadata")
            }
            
        except ValueError as e:
            logger.error("%s: %s", exam_id, e)
            result_message = {
                "exam_id": exam_id,
                "video_type": "pose_imitation",
                "status": "failed",
                "error": str(e),
                "metadata": task.get("metadata")
            }
            
        except Exception as e:
            logger.exception("작업 %s 실패", exam_id)
            result_message = {
                "exam_id": exam_id,
                "video_type": "pose_imitation",
                "status": "failed",
                "error": str(e),
                "metadata": task.get("metadata")
            }
            
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
            queue=self.config.task_queue,
            on_message_callback=self.process_message
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
    worker = PoseWorker()
    worker.start()