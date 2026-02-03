# AI/services/pose-estimation/app/worker.py
"""RabbitMQ 컨슈머 (메시지 수신 및 처리)"""

import json
import time
import io
import uuid
import logging
from typing import Any
from datetime import datetime, timezone, timedelta

import pika
import requests
from PIL import Image

from app.config import settings
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
    """RabbitMQ 메시지 컨슈머"""
    
    def __init__(self):
        self.model = get_model()
        self.analyzer = MotionAnalyzer()  # pose_imitation 분석용
        self.connection = None
        self.channel = None
    
    def connect(self):
        """RabbitMQ 연결"""
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD
        )
        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # 큐 선언
        self.channel.queue_declare(queue=settings.TASK_QUEUE, durable=True)
        self.channel.queue_declare(queue=settings.RESULT_QUEUE, durable=True)
        
        print(f"✅ RabbitMQ에 연결됨: {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
    
    def publish_result(self, result: dict):
        """결과를 Result Queue로 발행"""
        self.channel.basic_publish(
            exchange="",
            routing_key=settings.RESULT_QUEUE,
            body=json.dumps(result),
            properties=pika.BasicProperties(
                delivery_mode=2,  # 메시지 영속성
                content_type="application/json"
            )
        )
    
    def process_message(self, ch, method, properties, body):
        """메시지 처리 콜백 (타입별 분기)"""
        task = json.loads(body)
        task_type = task.get("type", "pose_detection")
        
        if task_type == "pose_imitation":
            result_message = self._process_pose_imitation(task)
        else:
            result_message = self._process_pose_detection(task)
        
        self.publish_result(result_message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def _process_pose_detection(self, task: dict) -> dict:
        """단일 이미지 포즈 감지 처리 (기존 로직)"""
        start_time = time.time()
        task_id = task.get("task_id", "unknown")
        print(f"✅ 작업 수신 [pose_detection]: {task_id}")
        
        try:
            # 이미지 로드
            image = self._load_image(task)
            
            # 추론
            threshold = task.get("threshold", settings.DEFAULT_THRESHOLD)
            results = self.model.detect(image, threshold)
            
            # 결과 발행
            result_message = {
                "task_id": task_id,
                "status": "success",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "data": {
                    "person_count": len(results),
                    "results": results
                },
                "metadata": task.get("metadata", {})
            }
            
            print(f"✅ 작업 {task_id} 완료: {len(results)}명 감지됨")
            
        except Exception as e:
            result_message = {
                "task_id": task_id,
                "status": "failed",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": {
                    "message": str(e),
                    "type": type(e).__name__
                },
                "metadata": task.get("metadata", {})
            }
            print(f"❌ 작업 {task_id} 실패: {e}")
        
        return result_message
    
    def _process_pose_imitation(self, task: dict) -> dict:
        """
        pose_imitation 요청 처리.
        
        Args:
            task: RabbitMQ 메시지
                - request_id: 요청 ID (선택, 없으면 자동 생성)
                - video_path: 영상 경로
                - name: 아동 이름 (로깅용)
                - age_months: 아동 월령 (12-24개월)
                
        Returns:
            PoseImitationResponse.to_dict() 형태의 응답
        """
        request_id = task.get("request_id", str(uuid.uuid4()))
        
        # KST 타임스탬프
        kst = timezone(timedelta(hours=9))
        analyzed_at = datetime.now(kst).isoformat()
        
        try:
            age_months = task["age_months"]
            name = task.get("name", "unknown")
            video_path = task["video_path"]
            
            # 월령에 따른 동작 세트 자동 결정
            action_list = get_action_set_by_age(age_months)
            
            logger.info(f" pose_imitation 분석 시작: {name} ({age_months}개월)")
            logger.info(f"   동작 세트: {action_list}")
            print(f"✅ 작업 수신 [pose_imitation]: {request_id} - {name} ({age_months}개월)")
            
            # 분석 수행
            result = self.analyzer.analyze_multi_trial(
                video_path=video_path,
                action_list=action_list,
                age_months=age_months
            )
            
            # 간결한 응답 생성
            response = PoseImitationResponse(
                request_id=request_id,
                analyzed_at=analyzed_at,
                status="completed",
                metrics=result.metrics,
                ados=result.ados
            )
            
            success_count = sum(1 for t in result.metrics["per_trial"] if t["success"])
            print(f"✅ 작업 {request_id} 완료: {success_count}/3 성공")
            logger.info(f" ADOS 결과: {result.ados}")
            
            return response.to_dict()
            
        except KeyError as e:
            error_msg = f"필수 필드 누락: {e}"
            logger.error(f"❌ {request_id}: {error_msg}")
            return {
                "request_id": request_id,
                "analyzed_at": analyzed_at,
                "status": "failed",
                "error": {
                    "type": "KeyError",
                    "message": error_msg
                }
            }
        except ValueError as e:
            logger.error(f"❌ {request_id}: {e}")
            return {
                "request_id": request_id,
                "analyzed_at": analyzed_at,
                "status": "failed",
                "error": {
                    "type": "ValueError",
                    "message": str(e)
                }
            }
        except Exception as e:
            logger.error(f"❌ {request_id}: {e}")
            return {
                "request_id": request_id,
                "analyzed_at": analyzed_at,
                "status": "failed",
                "error": {
                    "type": type(e).__name__,
                    "message": str(e)
                }
            }
    
    def _load_image(self, task: dict) -> Image.Image:
        """이미지 로드 (URL 또는 Base64)"""
        if "image_url" in task:
            response = requests.get(task["image_url"], timeout=30)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert("RGB")
        
        elif "image_base64" in task:
            import base64
            image_data = base64.b64decode(task["image_base64"])
            return Image.open(io.BytesIO(image_data)).convert("RGB")
        
        elif "file_path" in task:
            return Image.open(task["file_path"]).convert("RGB")
        
        else:
            raise ValueError("이미지 소스가 제공되지 않았습니다 (image_url, image_base64, 또는 file_path 중 하나 필요)")
    
    def start(self):
        """워커 시작"""
        self.connect()
        
        # prefetch_count=1: 한 번에 하나씩 처리
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=settings.TASK_QUEUE,
            on_message_callback=self.process_message
        )
        
        print(f"✅ 워커 시작됨. '{settings.TASK_QUEUE}' 큐에서 작업 대기 중...")
        print("   종료하려면 CTRL+C를 누르세요")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\n✅ 워커 종료 중...")
            self.channel.stop_consuming()
        finally:
            if self.connection:
                self.connection.close()


if __name__ == "__main__":
    worker = PoseWorker()
    worker.start()