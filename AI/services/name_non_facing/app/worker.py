# services/name_non_facing/app/worker.py
"""
RabbitMQ 메시지 컨슈머 워커

비대면 호명반응 분석 요청을 RabbitMQ에서 수신하여 처리합니다.

실행 방법:
    python -m app.worker

Reference:
    - pika: https://pika.readthedocs.io/en/stable/
"""

import threading
import queue
import base64
import contextlib
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, Optional

import pika
import requests
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from app.config import get_settings
from app.services.rabbitmq import RabbitMQService
from app.pipeline.orchestrator import FullPipelineOrchestrator

logger = logging.getLogger(__name__)


class NameNonFacingWorker:
    """
    비대면 호명반응 분석 워커
    
    RabbitMQ에서 작업 요청을 수신하고, 파이프라인을 실행하여 결과를 발행합니다.
    
    Message Flow:
        INPUT_QUEUE → Worker → OUTPUT_QUEUE
    
    Usage:
        worker = NameNonFacingWorker()
        worker.start()
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.rabbitmq = RabbitMQService()
        self.orchestrator: Optional[FullPipelineOrchestrator] = None
        
    def _init_orchestrator(self) -> None:
        """파이프라인 오케스트레이터 지연 초기화"""
        if self.orchestrator is None:
            logger.info("🔧 FullPipelineOrchestrator 초기화 중...")
            self.orchestrator = FullPipelineOrchestrator()
            logger.info("✅ FullPipelineOrchestrator 초기화 완료")
    
    def connect(self) -> None:
        """RabbitMQ 연결"""
        self.rabbitmq.connect()
        self.rabbitmq.declare_queues()
    
    def process_message(
        self,
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes
    ) -> None:
        """
        메시지 처리 콜백 (Threaded Implementation)
        
        1. 메시지 파싱
        2. 비디오 로드
        3. 파이프라인 실행 (별도 스레드)
        4. Heartbeat 유지 (메인 스레드)
        5. 결과 발행
        """
        start_time = time.time()
        task = json.loads(body)
        
        # BE는 camelCase로 전송
        exam_id = task.get("examId", "unknown")
        video_id = task.get("videoId", "unknown")
        child_name = task.get("childName", "아이")
        age_months = task.get("ageMonths")
        
        logger.info("=" * 60)
        logger.info(f"!!!!!!!!!!!! 작업 수신: examId={exam_id}, videoId={video_id}")
        logger.info(f"   childName={child_name}, ageMonths={age_months}")
        logger.info("=" * 60)
        
        tmp_path: Optional[str] = None
        result_queue = queue.Queue()
        
        try:
            # 오케스트레이터 초기화 (최초 1회)
            self._init_orchestrator()
            
            # 비디오 로드 (IO 바운드 작업이지만 짧으므로 메인 스레드에서 처리)
            video_path = self._load_video(task)
            tmp_path = video_path if video_path != task.get("video_path") else None
            
            # 작업 스레드 함수 정의
            def run_pipeline_thread():
                try:
                    logger.info("🧵 작업 스레드 시작...")
                    pipeline_result = self.orchestrator.run(
                        video_path=video_path,
                        child_name=child_name,
                        request_id=exam_id
                    )
                    result_queue.put({"status": "success", "data": pipeline_result})
                except Exception as e:
                    logger.exception("❌ 작업 스레드 예외 발생")
                    result_queue.put({"status": "error", "error": e})
                finally:
                    logger.info("🧵 작업 스레드 종료")

            # 스레드 시작 (Daemon=True: 메인 프로세스 종료 시 함께 종료)
            worker_thread = threading.Thread(target=run_pipeline_thread, daemon=True)
            worker_thread.start()
            
            # 스레드가 살아있는 동안 Heartbeat 유지
            while worker_thread.is_alive():
                # process_data_events를 호출하여 Pika가 소켓 이벤트를 처리하고 Heartbeat를 보내도록 함
                self.rabbitmq.connection.process_data_events(time_limit=1)
                
                # 짧게 대기하여 CPU 과점 방지 (Pika sleep 권장)
                # sleep 내부에서도 process_data_events가 호출될 수 있음
                self.rabbitmq.connection.sleep(1.0)
            
            # 스레드 종료 대기 및 결과 수신
            worker_thread.join()
            thread_result = result_queue.get_nowait()
            
            if thread_result["status"] == "success":
                pipeline_result = thread_result["data"]
                
                # 성공 응답 생성
                result_message = {
                    "examId": exam_id,
                    "videoId": video_id,
                    "videoType": "NAME_NON_FACING",
                    "analyzedAt": datetime.now().isoformat(),
                    "status": "SUCCESS",
                    "metrics": pipeline_result.get("metrics"),
                    "ADOS": pipeline_result.get("ADOS"),
                }
                
                # 결과 요약 로깅
                per_trial = pipeline_result.get("metrics", {}).get("per_trial", [])
                success_count = sum(1 for t in per_trial if t.get("success"))
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"✅ 작업 완료: examId={exam_id}, "
                    f"success={success_count}/{len(per_trial)}, "
                    f"time={elapsed_ms:.0f}ms"
                )
            else:
                # 스레드 내부 예외 재발생
                raise thread_result["error"]
            
        except Exception as e:
            # 실패 응답 생성
            result_message = {
                "examId": exam_id,
                "videoId": video_id,
                "videoType": "NAME_NON_FACING",
                "analyzedAt": datetime.now().isoformat(),
                "status": "FAILED",
                "metrics": None,
                "ADOS": None,
            }
            logger.exception(f"❌ 작업 실패: exam_id={exam_id}")
            
        finally:
            # 임시 파일 정리
            if tmp_path and os.path.exists(tmp_path):
                with contextlib.suppress(Exception):
                    os.remove(tmp_path)
                    logger.debug(f"📥 임시 파일 삭제: {tmp_path}")
        
        # 결과 발행 (메인 스레드에서 안전하게 수행)
        self.rabbitmq.publish(self.settings.OUTPUT_QUEUE, result_message)
        
        # ACK 전송
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def _load_video(self, task: dict) -> str:
        """
        S3 URL에서 비디오 다운로드
        
        Args:
            task: 작업 메시지 (s3Uri 필드 필수)
            
        Returns:
            다운로드된 비디오 파일 경로
            
        Raises:
            ValueError: s3Uri가 없거나 다운로드 실패
        """
        s3_url = task.get("s3Uri")
        if not s3_url:
            raise ValueError("s3Uri 필드가 필요합니다")
        
        logger.info(f"📥 S3에서 비디오 다운로드: {s3_url}")
        
        response = requests.get(s3_url, timeout=120)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=".mp4",
            prefix="nnf_"
        ) as tmp:
            tmp.write(response.content)
            logger.info(f"📥 다운로드 완료: {tmp.name}")
            return tmp.name
    
    def start(self) -> None:
        """
        워커 시작 (blocking)
        
        RabbitMQ에서 메시지를 수신하고 처리합니다.
        CTRL+C로 종료할 수 있습니다.
        """
        self.connect()
        
        # prefetch_count=1: 한 번에 하나씩 처리
        self.rabbitmq.channel.basic_qos(prefetch_count=1)
        
        self.rabbitmq.channel.basic_consume(
            queue=self.settings.INPUT_QUEUE,
            on_message_callback=self.process_message
        )
        
        logger.info("=" * 60)
        logger.info(f"📥 Worker 시작됨")
        logger.info(f"   요청 큐: {self.settings.INPUT_QUEUE}")
        logger.info(f"   응답 큐: {self.settings.OUTPUT_QUEUE}")
        logger.info(f"   종료하려면 CTRL+C를 누르세요")
        logger.info("=" * 60)
        
        try:
            self.rabbitmq.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("📥 Worker 종료 중...")
            self.rabbitmq.channel.stop_consuming()
        finally:
            self.rabbitmq.close()
            logger.info("📥 Worker 종료됨")

def main():
    """Worker 진입점"""
    # 로깅 설정
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Worker 시작
    worker = NameNonFacingWorker()
    worker.start()


if __name__ == "__main__":
    main()
