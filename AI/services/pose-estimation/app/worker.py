# app/worker.py
"""RabbitMQ 컨슈머 (메시지 수신 및 처리)"""

import json
import time
import io
from typing import Any

import pika
import requests
from PIL import Image

from app.config import settings
from app.models.vitpose import get_model


class PoseWorker:
    """RabbitMQ 메시지 컨슈머"""
    
    def __init__(self):
        self.model = get_model()
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
        """메시지 처리 콜백"""
        start_time = time.time()
        task = json.loads(body)
        
        task_id = task.get("task_id", "unknown")
        print(f"✅ 작업 수신: {task_id}")
        
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
                "person_count": len(results),
                "results": results,
                "metadata": task.get("metadata")
            }
            
            print(f"✅ 작업 {task_id} 완료: {len(results)}명 감지됨")
            
        except Exception as e:
            result_message = {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "metadata": task.get("metadata")
            }
            print(f"❌ 작업 {task_id} 실패: {e}")
        
        self.publish_result(result_message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
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
        
        print(f"✅👷 워커 시작됨. '{settings.TASK_QUEUE}' 큐에서 작업 대기 중...")
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