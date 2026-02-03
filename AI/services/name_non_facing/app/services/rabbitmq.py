# services/name_non_facing/app/services/rabbitmq.py
"""
RabbitMQ 연결 및 메시지 발행 서비스

RabbitMQ와의 연결을 관리하고, 큐 선언 및 메시지 발행 기능을 제공합니다.

Reference:
    - pika: https://pika.readthedocs.io/en/stable/
    - RabbitMQ Tutorial: https://www.rabbitmq.com/tutorials/tutorial-one-python.html
"""

import json
import logging
import time
from typing import Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError

from app.config import get_settings

logger = logging.getLogger(__name__)


class RabbitMQService:
    """
    RabbitMQ 연결 및 메시지 발행 관리 클래스

    Features:
        - 연결 수립 및 재연결 (지수 백오프)
        - 큐 선언 (durable)
        - JSON 메시지 발행

    Usage:
        service = RabbitMQService()
        service.connect()
        service.publish("queue_name", {"key": "value"})
        service.close()
    """

    def __init__(self):
        self.settings = get_settings()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
    
    def connect(self) -> None:
        """
        RabbitMQ 연결 수립

        지수 백오프로 최대 RABBITMQ_MAX_RETRIES 회 재시도합니다.
        """
        retry_delay = self.settings.RABBITMQ_INITIAL_RETRY_DELAY
        max_retries = self.settings.RABBITMQ_MAX_RETRIES

        for attempt in range(1, max_retries + 1):
            try:
                credentials = pika.PlainCredentials(
                    self.settings.RABBITMQ_USER,
                    self.settings.RABBITMQ_PASSWORD
                )
                parameters = pika.ConnectionParameters(
                    host=self.settings.RABBITMQ_HOST,
                    port=self.settings.RABBITMQ_PORT,
                    virtual_host=self.settings.RABBITMQ_VHOST,
                    credentials=credentials,
                    heartbeat=self.settings.RABBITMQ_HEARTBEAT,
                    blocked_connection_timeout=self.settings.RABBITMQ_BLOCKED_CONNECTION_TIMEOUT,
                )
                
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                logger.info(
                    "✅ RabbitMQ 연결 성공: %s:%s",
                    self.settings.RABBITMQ_HOST,
                    self.settings.RABBITMQ_PORT
                )
                return
                
            except AMQPConnectionError as e:
                logger.warning(
                    "⚠️ RabbitMQ 연결 실패 (시도 %d/%d): %s",
                    attempt, max_retries, e
                )
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                else:
                    logger.error("❌ RabbitMQ 연결 최대 재시도 횟수 초과")
                    raise
    
    def declare_queues(self) -> None:
        """
        필요한 큐 선언
        
        durable=True로 설정하여 RabbitMQ 재시작 후에도 큐가 유지됩니다.
        """
        if not self.channel:
            raise RuntimeError("RabbitMQ에 연결되지 않음. connect()를 먼저 호출하세요.")
        
        # 요청 큐
        self.channel.queue_declare(
            queue=self.settings.INPUT_QUEUE,
            durable=True
        )
        logger.info("!!!!!! 요청 큐 선언: %s", self.settings.INPUT_QUEUE)
        
        # 응답 큐
        self.channel.queue_declare(
            queue=self.settings.OUTPUT_QUEUE,
            durable=True
        )
        logger.info("!!!! 응답 큐 선언: %s", self.settings.OUTPUT_QUEUE)
    
    def publish(self, queue: str, message: dict) -> None:
        """
        JSON 메시지 발행
        
        Args:
            queue: 대상 큐 이름
            message: 발행할 메시지 (dict → JSON 직렬화)
        """
        if not self.channel:
            raise RuntimeError("RabbitMQ에 연결되지 않음. connect()를 먼저 호출하세요.")
        
        body = json.dumps(message, ensure_ascii=False, default=str)
        
        self.channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # 메시지 영속성
                content_type="application/json",
            )
        )
        logger.debug("!!!!!! 메시지 발행: %s → %s", queue, body[:100])
    
    def close(self) -> None:
        """연결 종료"""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("!!!!!! RabbitMQ 연결 종료")
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return (
            self.connection is not None 
            and self.connection.is_open
            and self.channel is not None
            and self.channel.is_open
        )
