# services/name_non_facing/app/main.py
"""
FastAPI Health Check API

서비스 상태 및 RabbitMQ 연결 상태를 확인하는 API입니다.

실행 방법:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    
    또는 Docker에서:
    docker run -e RUN_MODE=api ...

Reference:
    - FastAPI: https://fastapi.tiangolo.com/
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import get_settings
from app.services.rabbitmq import RabbitMQService

logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Name Non-Facing API",
    description="비대면 호명반응 분석 서비스 Health Check API",
    version="1.0.0",
)

# RabbitMQ 서비스 (상태 확인용)
_rabbitmq: Optional[RabbitMQService] = None


class HealthResponse(BaseModel):
    """Health Check 응답"""
    status: str
    service: str
    rabbitmq: str
    timestamp: str


class ReadyResponse(BaseModel):
    """Readiness Check 응답"""
    ready: bool
    message: str


class InfoResponse(BaseModel):
    """서비스 정보 응답"""
    service: str
    version: str
    video_type: str
    input_queue: str
    output_queue: str


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 RabbitMQ 연결 시도"""
    global _rabbitmq
    settings = get_settings()
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    
    try:
        _rabbitmq = RabbitMQService()
        _rabbitmq.connect()
        logger.info("✅ RabbitMQ 연결 성공 (Health API)")
    except Exception as e:
        logger.warning(f"⚠️ RabbitMQ 연결 실패 (Health API): {e}")
        _rabbitmq = None


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 RabbitMQ 연결 해제"""
    global _rabbitmq
    if _rabbitmq:
        _rabbitmq.close()
        logger.info("🔌 RabbitMQ 연결 종료 (Health API)")


@app.get("/", response_model=InfoResponse)
async def root():
    """서비스 정보"""
    settings = get_settings()
    return InfoResponse(
        service="name_non_facing",
        version="1.0.0",
        video_type="NAME_NON_FACING",
        input_queue=settings.INPUT_QUEUE,
        output_queue=settings.OUTPUT_QUEUE,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    서비스 상태 확인
    
    RabbitMQ 연결 상태를 포함한 서비스 상태를 반환합니다.
    """
    rabbitmq_status = "disconnected"
    
    if _rabbitmq and _rabbitmq.is_connected():
        rabbitmq_status = "connected"
    
    return HealthResponse(
        status="healthy",
        service="name_non_facing",
        rabbitmq=rabbitmq_status,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """
    준비 상태 확인
    
    RabbitMQ에 연결되어 있어야 ready 상태입니다.
    """
    if _rabbitmq and _rabbitmq.is_connected():
        return ReadyResponse(
            ready=True,
            message="Service is ready to process messages",
        )
    else:
        return ReadyResponse(
            ready=False,
            message="RabbitMQ connection not established",
        )


@app.get("/ping")
async def ping():
    """간단한 ping 확인"""
    return {"pong": True}