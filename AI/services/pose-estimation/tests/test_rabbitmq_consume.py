#!/usr/bin/env python
"""
RabbitMQ 결과 큐에서 메시지 확인 (pose-estimation)

Usage:
    python tests/test_rabbitmq_consume.py           # 하나만 가져오기
    python tests/test_rabbitmq_consume.py --wait    # 메시지 올 때까지 대기
    python tests/test_rabbitmq_consume.py --all     # 모든 메시지 가져오기
"""

import argparse
import json
import sys

import pika

# 기본 설정
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5672
DEFAULT_USER = "guest"
DEFAULT_PASSWORD = "guest"
DEFAULT_QUEUE = "pose_result_queue"


def get_single_message(channel, queue: str, auto_ack: bool = True) -> dict | None:
    """큐에서 메시지 하나 가져오기"""
    method, properties, body = channel.basic_get(queue=queue, auto_ack=auto_ack)

    if body:
        return json.loads(body)
    return None


def consume_all_messages(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    queue: str = DEFAULT_QUEUE,
) -> list[dict]:
    """큐의 모든 메시지 가져오기"""
    credentials = pika.PlainCredentials(DEFAULT_USER, DEFAULT_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials,
    )

    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
    except pika.exceptions.AMQPConnectionError as e:
        print(f"[ERROR] RabbitMQ 연결 실패: {e}")
        sys.exit(1)

    # 큐 선언 (없으면 생성)
    channel.queue_declare(queue=queue, durable=True)

    messages = []
    while True:
        msg = get_single_message(channel, queue)
        if msg is None:
            break
        messages.append(msg)

    connection.close()
    return messages


def consume_one_message(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    queue: str = DEFAULT_QUEUE,
) -> dict | None:
    """큐에서 메시지 하나만 가져오기"""
    credentials = pika.PlainCredentials(DEFAULT_USER, DEFAULT_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials,
    )

    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
    except pika.exceptions.AMQPConnectionError as e:
        print(f"[ERROR] RabbitMQ 연결 실패: {e}")
        sys.exit(1)

    # 큐 선언 (없으면 생성)
    channel.queue_declare(queue=queue, durable=True)

    msg = get_single_message(channel, queue)
    connection.close()
    return msg


def wait_for_message(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    queue: str = DEFAULT_QUEUE,
    timeout: int = 300,
) -> dict | None:
    """메시지가 올 때까지 대기"""
    credentials = pika.PlainCredentials(DEFAULT_USER, DEFAULT_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials,
    )

    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
    except pika.exceptions.AMQPConnectionError as e:
        print(f"[ERROR] RabbitMQ 연결 실패: {e}")
        sys.exit(1)

    # 큐 선언 (없으면 생성)
    channel.queue_declare(queue=queue, durable=True)

    print(f"[INFO] '{queue}' 큐에서 메시지 대기 중... (최대 {timeout}초)")
    print("       Ctrl+C로 중단")

    result = {"message": None}

    def callback(ch, method, properties, body):
        result["message"] = json.loads(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        ch.stop_consuming()

    channel.basic_consume(queue=queue, on_message_callback=callback)

    try:
        connection.process_data_events(time_limit=timeout)
    except KeyboardInterrupt:
        print("\n[INFO] 대기 중단됨")

    connection.close()
    return result["message"]


def print_message(msg: dict | None, index: int | None = None) -> None:
    """메시지 출력"""
    if msg is None:
        print("[INFO] 메시지 없음")
        return

    prefix = f"[{index}] " if index is not None else ""
    status = msg.get("status", "unknown")
    exam_id = msg.get("examId", "unknown")

    status_icon = "[OK]" if status == "SUCCESS" else "[FAIL]"

    print(f"{prefix}{status_icon} examId={exam_id}, status={status}")

    if status == "SUCCESS":
        metrics = msg.get("metrics", {})
        per_trial = metrics.get("per_trial", [])
        success_count = sum(1 for t in per_trial if t.get("success"))
        print(f"     성공: {success_count}/{len(per_trial)}")
        print(f"     ADOS: {msg.get('ADOS')}")
    else:
        print(f"     에러: {msg.get('error')}")

    print()
    print("상세 응답:")
    print(json.dumps(msg, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="RabbitMQ 결과 큐 메시지 확인 (pose-estimation)")
    parser.add_argument(
        "--wait", "-w",
        action="store_true",
        help="메시지가 올 때까지 대기",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="큐의 모든 메시지 가져오기",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=300,
        help="대기 타임아웃 (초, 기본: 300)",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"RabbitMQ 호스트 (기본: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"RabbitMQ 포트 (기본: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--queue", "-q",
        default=DEFAULT_QUEUE,
        help=f"결과 큐 이름 (기본: {DEFAULT_QUEUE})",
    )

    args = parser.parse_args()

    print("=" * 60)
    print(f"RabbitMQ 결과 큐 확인: {args.queue}")
    print("=" * 60)

    if args.all:
        messages = consume_all_messages(
            host=args.host,
            port=args.port,
            queue=args.queue,
        )
        print(f"[INFO] 총 {len(messages)}개 메시지 수신")
        print()
        for i, msg in enumerate(messages, 1):
            print("-" * 40)
            print_message(msg, i)
    elif args.wait:
        msg = wait_for_message(
            host=args.host,
            port=args.port,
            queue=args.queue,
            timeout=args.timeout,
        )
        print_message(msg)
    else:
        msg = consume_one_message(
            host=args.host,
            port=args.port,
            queue=args.queue,
        )
        print_message(msg)


if __name__ == "__main__":
    main()
