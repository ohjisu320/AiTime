#!/usr/bin/env python
"""
RabbitMQ 요청 큐에 목업 메시지 발행 (pose-estimation)

Usage:
    python tests/test_rabbitmq_publish.py
    python tests/test_rabbitmq_publish.py --video sample_video/pose_hurray_F.mp4
    python tests/test_rabbitmq_publish.py --child-name "홍길동" --age 18
"""

import argparse
import json
import sys
from pathlib import Path

import pika

# 기본 설정
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5672
DEFAULT_USER = "guest"
DEFAULT_PASSWORD = "guest"
DEFAULT_QUEUE = "pose_task_queue"


def publish_mock_message(
    video_path: str = "sample_video/pose_hurray_F.mp4",
    child_name: str = "테스트아이",
    age_months: int = 18,
    exam_id: str = "test-exam-001",
    video_id: str = "test-video-001",
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    queue: str = DEFAULT_QUEUE,
) -> None:
    """목업 메시지 발행"""

    # 비디오 경로 확인
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"[ERROR] 비디오 파일을 찾을 수 없습니다: {video_path}")
        print(f"        현재 디렉토리: {Path.cwd()}")
        sys.exit(1)

    # RabbitMQ 연결
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
        print(f"        호스트: {host}:{port}")
        print("        Docker RabbitMQ가 실행 중인지 확인하세요.")
        sys.exit(1)

    # 큐 선언 (없으면 생성)
    channel.queue_declare(queue=queue, durable=True)

    # 목업 메시지 생성 (BE_to_AI_by_rabbitmq.json 구조)
    message = {
        "examId": exam_id,
        "videoId": video_id,
        "videoType": "POSE_IMITATION",
        "childName": child_name,
        "ageMonths": age_months,
        "video_path": str(video_file.absolute()),  # 로컬 테스트용 경로
        # "s3Uri": "s3://your-bucket/videos/vid_0001.mp4"  # 실제 환경에서는 이 필드 사용
    }

    # 메시지 발행
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=json.dumps(message, ensure_ascii=False),
        properties=pika.BasicProperties(
            delivery_mode=2,  # 메시지 영속성
            content_type="application/json",
        ),
    )

    print("=" * 60)
    print("[SUCCESS] 메시지 발행 완료")
    print("=" * 60)
    print(f"  큐: {queue}")
    print(f"  메시지:")
    print(json.dumps(message, indent=4, ensure_ascii=False))
    print("=" * 60)

    connection.close()


def main():
    parser = argparse.ArgumentParser(description="RabbitMQ 목업 메시지 발행 (pose-estimation)")
    parser.add_argument(
        "--video", "-v",
        default="sample_video/pose_hurray_F.mp4",
        help="비디오 파일 경로 (기본: sample_video/pose_hurray_F.mp4)",
    )
    parser.add_argument(
        "--child-name", "-n",
        default="테스트아이",
        help="아이 이름 (기본: 테스트아이)",
    )
    parser.add_argument(
        "--age", "-a",
        type=int,
        default=18,
        help="아이 월령 (기본: 18)",
    )
    parser.add_argument(
        "--exam-id",
        default="test-exam-001",
        help="검사 ID (기본: test-exam-001)",
    )
    parser.add_argument(
        "--video-id",
        default="test-video-001",
        help="비디오 ID (기본: test-video-001)",
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
        help=f"요청 큐 이름 (기본: {DEFAULT_QUEUE})",
    )

    args = parser.parse_args()

    publish_mock_message(
        video_path=args.video,
        child_name=args.child_name,
        age_months=args.age,
        exam_id=args.exam_id,
        video_id=args.video_id,
        host=args.host,
        port=args.port,
        queue=args.queue,
    )


if __name__ == "__main__":
    main()
