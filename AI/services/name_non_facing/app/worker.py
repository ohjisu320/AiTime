# services/name_non_facing/app/worker.py
"""
RabbitMQ 메시지 컨슈머 워커

비대면 호명반응 분석 요청을 RabbitMQ에서 수신하여 처리합니다.

실행 방법:
    python -m app.worker

Reference:
    - pika: https://pika.readthedocs.io/en/stable/
"""

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
        메시지 처리 콜백
        
        1. 메시지 파싱
        2. 비디오 로드
        3. 파이프라인 실행
        4. 결과 발행
        """
        start_time = time.time()
        task = json.loads(body)
        
        exam_id = task.get("exam_id", "unknown")
        child_name = task.get("child_name", "아이")
        
        logger.info("=" * 60)
        logger.info(f"!!!!!!!!!!!! 작업 수신: exam_id={exam_id}")
        logger.info(f"   child_name={child_name}")
        logger.info("=" * 60)
        
        tmp_path: Optional[str] = None
        result_message: Dict[str, Any] = {}
        
        try:
            # 오케스트레이터 초기화 (최초 1회)
            self._init_orchestrator()
            
            # 비디오 로드
            video_path = self._load_video(task)
            tmp_path = video_path if video_path != task.get("video_path") else None
            
            # 파이프라인 실행
            pipeline_result = self.orchestrator.run(
                video_path=video_path,
                child_name=child_name,
                request_id=exam_id
            )
            
            # 성공 응답 생성
            processing_time_ms = (time.time() - start_time) * 1000
            
            result_message = {
                "exam_id": exam_id,
                "video_type": "NAME_NON_FACING",
                "analyzed_at": datetime.now().isoformat(),
                "status": "completed",
                "processing_time_ms": round(processing_time_ms, 2),
                "metrics": pipeline_result.get("metrics"),
                "ADOS": pipeline_result.get("ADOS"),
                "error": None
            }
            
            # 결과 요약 로깅
            per_trial = pipeline_result.get("metrics", {}).get("per_trial", [])
            success_count = sum(1 for t in per_trial if t.get("success"))
            logger.info(
                f"✅ 작업 완료: exam_id={exam_id}, "
                f"success={success_count}/{len(per_trial)}, "
                f"time={processing_time_ms:.0f}ms"
            )
            
        except Exception as e:
            # 실패 응답 생성
            processing_time_ms = (time.time() - start_time) * 1000
            
            result_message = {
                "exam_id": exam_id,
                "video_type": "NAME_NON_FACING",
                "analyzed_at": datetime.now().isoformat(),
                "status": "failed",
                "processing_time_ms": round(processing_time_ms, 2),
                "metrics": None,
                "ADOS": None,
                "error": str(e)
            }
            
            logger.exception(f"❌ 작업 실패: exam_id={exam_id}")
            
        finally:
            # 임시 파일 정리
            if tmp_path and os.path.exists(tmp_path):
                with contextlib.suppress(Exception):
                    os.remove(tmp_path)
                    logger.debug(f"📥 임시 파일 삭제: {tmp_path}")
        
        # 결과 발행
        self.rabbitmq.publish(self.settings.OUTPUT_QUEUE, result_message)
        
        # ACK 전송 (메시지 처리 완료)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def _load_video(self, task: dict) -> str:
        """
        비디오 소스 로드
        
        Args:
            task: 작업 메시지
            
        Returns:
            비디오 파일 경로
            
        Raises:
            ValueError: 비디오 소스가 없거나 로드 실패
        """
        # 옵션 1: 로컬 경로
        if "video_path" in task:
            path = task["video_path"]
            if not os.path.exists(path):
                raise ValueError(f"비디오 경로를 찾을 수 없음: {path}")
            logger.info(f"📥 로컬 비디오: {path}")
            return path
        
        # 옵션 2: URL 다운로드
        if "video_url" in task:
            url = task["video_url"]
            logger.info(f"📥 URL에서 비디오 다운로드: {url}")
            
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=".mp4",
                prefix="nnf_"
            ) as tmp:
                tmp.write(response.content)
                logger.info(f"📥 다운로드 완료: {tmp.name}")
                return tmp.name
        
        # 옵션 3: Base64 디코딩
        if "video_base64" in task:
            logger.info("📥 Base64 디코딩 중...")
            video_data = base64.b64decode(task["video_base64"])
            
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=".mp4",
                prefix="nnf_"
            ) as tmp:
                tmp.write(video_data)
                logger.info(f"📥 디코딩 완료: {tmp.name}")
                return tmp.name
        
        raise ValueError(
            "비디오 소스가 제공되지 않음 "
            "(video_path, video_url, 또는 video_base64 중 하나 필요)"
        )
    
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
