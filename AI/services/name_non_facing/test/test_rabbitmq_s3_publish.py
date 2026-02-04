#!/usr/bin/env python
"""
RabbitMQ + S3 URL 테스트용 Producer (name_non_facing)

BE에서 S3 URL을 전달하는 것을 시뮬레이션합니다.
Worker가 S3에서 영상을 다운로드하여 분석을 수행합니다.

Usage:
    python test/test_rabbitmq_s3_publish.py --s3-url "https://your-s3-url.mp4"
    python test/test_rabbitmq_s3_publish.py --s3-url "https://..." --name "홍길동"
"""

import argparse
import json
import os
import sys

import pika

# 기본 설정 (환경 변수 우선)
DEFAULT_HOST = os.getenv("RABBITMQ_HOST", "localhost")
DEFAULT_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
DEFAULT_USER = os.getenv("RABBITMQ_USER", "guest")
DEFAULT_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
DEFAULT_INPUT_QUEUE = os.getenv("INPUT_QUEUE", "analysis.name_non_facing.request")


def publish_s3_message(
    s3_url: str,
    child_name: str = "테스트아이",
    exam_id: str = "test-exam-nnf-001",
    video_id: str = "test-video-nnf-001",
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    queue: str = DEFAULT_INPUT_QUEUE,
) -> None:
    """S3 URL을 포함한 메시지 발행"""

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
        print("        docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management")
        sys.exit(1)

    # 큐 선언 (없으면 생성)
    channel.queue_declare(queue=queue, durable=True)

    # S3 URL 메시지 생성 (BE 스펙과 동일)
    message = {
        "examId": exam_id,
        "videoId": video_id,
        "videoType": "NAME_RESPONSE_NON_FACING",
        "childName": child_name,
        "s3Uri": s3_url,  # ★ S3 URL
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

    print("=" * 70)
    print("[SUCCESS] S3 URL 메시지 발행 완료 (name_non_facing)")
    print("=" * 70)
    print(f"  큐: {queue}")
    print(f"  아이 이름: {child_name}")
    print(f"  분석 내용: 이름 부르기 반응 (뒤통수/측면 감지)")
    print()
    print("  메시지 내용:")
    print(json.dumps(message, indent=4, ensure_ascii=False))
    print("=" * 70)
    print()
    print("[다음 단계]")
    print("  1. Worker 터미널에서 처리 로그 확인")
    print("  2. 결과 확인: python test/test_rabbitmq_consume.py --wait")

    connection.close()


def main():
    parser = argparse.ArgumentParser(
        description="RabbitMQ S3 URL 테스트 발행 (name_non_facing)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 테스트
  python test/test_rabbitmq_s3_publish.py \\
      --s3-url "https://bucket.s3.amazonaws.com/video.mp4"

  # 아이 이름 지정
  python test/test_rabbitmq_s3_publish.py \\
      --s3-url "https://bucket.s3.amazonaws.com/video.mp4" \\
      --name "김철수"
        """
    )
    
    parser.add_argument(
        "--s3-url", "-s",
        required=True,
        help="S3 URL (필수). 전체 URL을 따옴표로 감싸서 입력하세요.",
    )
    parser.add_argument(
        "--name", "-n",
        default="테스트아이",
        help="아이 이름 (기본: 테스트아이)",
    )
    parser.add_argument(
        "--exam-id",
        default="test-exam-nnf-001",
        help="검사 ID (기본: test-exam-nnf-001)",
    )
    parser.add_argument(
        "--video-id",
        default="test-video-nnf-001",
        help="비디오 ID (기본: test-video-nnf-001)",
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
        default=DEFAULT_INPUT_QUEUE,
        help=f"요청 큐 이름 (기본: {DEFAULT_INPUT_QUEUE})",
    )

    args = parser.parse_args()

    # S3 URL 기본 검증
    if not args.s3_url.startswith(("http://", "https://")):
        print(f"[ERROR] 올바른 URL 형식이 아닙니다: {args.s3_url}")
        print("        https://로 시작하는 URL을 입력하세요.")
        sys.exit(1)

    publish_s3_message(
        s3_url=args.s3_url,
        child_name=args.name,
        exam_id=args.exam_id,
        video_id=args.video_id,
        host=args.host,
        port=args.port,
        queue=args.queue,
    )


if __name__ == "__main__":
    main()
