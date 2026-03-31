# AI/services/pose-estimation/app/worker.py
"""RabbitMQ 컨슈머 (메시지 수신 및 처리)"""

import contextlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone, timedelta

import pika
import requests

from app.config import settings, RabbitMQConfig
from app.models.vitpose import get_model
from app.pipeline.analyzer import MotionAnalyzer

logger = logging.getLogger(__name__)

# 한국 표준시 (KST)
KST = timezone(timedelta(hours=9))

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
        """메시지 처리 콜백 (Threaded for Heartbeats)"""
        import threading
        import queue
        import time

        task = json.loads(body)

        # === BE → AI 필드 파싱 (camelCase) ===
        exam_id = task.get("examId")
        video_id = task.get("videoId")
        video_type = task.get("videoType")
        child_name = task.get("childName", "unknown")
        age_months = task.get("ageMonths")

        logger.info("작업 수신: examId=%s, videoType=%s", exam_id, video_type)

        tmp_path = None
        result_queue = queue.Queue()

        def analyze_wrapper():
            """별도 스레드에서 실행될 분석 로직"""
            try:
                # 비디오 로드
                video_path = self._load_video(task)
                # 로컬 경로인 경우 삭제하지 않음 (Wrapper 안에서 처리하거나, 메인에서 처리)
                # 여기서는 경로만 리턴하고 메인에서 cleanup 하는게 안전하지만,
                # 예외 발생 시 cleanup을 위해 try-finally 구조가 필요함.
                # 편의상 로드된 경로는 큐에 넣기 어렵으므로(복잡도 증가),
                # self._load_video는 메인 스레드에서 호출하는게 낫지만, 다운로드 시간도 길어질 수 있음.
                # 따라서 다운로드+분석을 모두 스레드에서 함.
                
                nonlocal tmp_path
                # 주의: tmp_path는 메인 스레드 변수이므로 쓰기 시 조심해야 하나,
                # 메인 스레드는 읽기만 하고(cleanup 시), 워커 스레드가 씀.
                # 하지만 로직 단순화를 위해 여기서 로컬 변수로 쓰고, 결과에 포함시켜 리턴하는게 나음.
                pass
            except Exception:
                pass

        # 실제 작업 함수 (복잡한 로직을 내부 함수로 분리)
        def target_function():
            _tmp_path = None
            try:
                # 1. 비디오 로드 (다운로드 포함)
                video_path = self._load_video(task)
                if "video_path" not in task:
                    _tmp_path = video_path

                # 2. 필수 필드 검증 & 동작 세트 결정
                if age_months is None:
                    raise KeyError("ageMonths")
                action_list = get_action_set_by_age(age_months)

                logger.info("pose_imitation 분석 시작: %s (%d개월)", child_name, age_months)
                logger.info("동작 세트: %s", action_list)
                # 3. 분석 수행
                _result = self.analyzer.analyze_multi_trial(
                    video_path=video_path,
                    action_list=action_list,
                    age_months=age_months
                )
                
                # 성공 결과 큐에 넣기
                result_queue.put({"status": "success", "data": _result, "tmp_path": _tmp_path})

            except Exception as e:
                # 실패 결과 큐에 넣기
                result_queue.put({"status": "error", "error": e, "tmp_path": _tmp_path})

        # 스레드 시작
        worker_thread = threading.Thread(target=target_function)
        worker_thread.start()

        # 타임아웃 설정 (3시간)
        TIMEOUT_SECONDS = 3 * 60 * 60 
        start_time = time.time()

        # Heartbeat Loop
        while worker_thread.is_alive():
            # RabbitMQ 연결 유지 (Heartbeat 전송)
            self.connection.process_data_events()
            
            # GIL Starvation 방지
            time.sleep(0.1)

            # 타임아웃 체크
            if time.time() - start_time > TIMEOUT_SECONDS:
                logger.error("작업 시간 초과 (%d초). 강제 중단 처리.", TIMEOUT_SECONDS)
                # 주의: 파이썬 스레드는 강제 종료 불가. 프로세스를 종료하거나, 플래그를 써야 함.
                # 여기서는 에러 응답 보내고 루프 탈출 -> 이후 컨테이너 재시작 등 고려해야 함.
                break

        # 스레드 종료 대기 (타임아웃 되었더라도 join은 필요하지만, 여기서는 바로 응답 보냄)
        # 정상 종료된 경우 결과 가져오기
        try:
            # 타임아웃 안 걸리고 끝났거나, 타임아웃으로 루프 탈출한 경우
            # get_nowait() 또는 timeout 있는 get() 사용
            # 스레드가 아직 살아있으면(타임아웃 케이스) 큐에 아무것도 없음 -> Empty 예외
            result_data = result_queue.get(timeout=1.0)
            
            # 임시 파일 경로 업데이트 (메인 스레드에서 삭제하기 위해)
            tmp_path = result_data.get("tmp_path")

            if result_data["status"] == "success":
                analysis_result = result_data["data"]
                # === AI → BE 응답 생성 ===
                result_message = {
                    "examId": exam_id,
                    "videoId": video_id,
                    "videoType": "POSE_IMITATION",
                    "analyzedAt": datetime.now(KST).isoformat(),
                    "status": "SUCCESS",
                    "metrics": analysis_result.metrics,
                    "ADOS": analysis_result.ados
                }
                success_count = sum(1 for t in analysis_result.metrics["per_trial"] if t["success"])
                logger.info("작업 %s 완료: %d/3 성공", exam_id, success_count)
            else:
                raise result_data["error"]

        except queue.Empty:
            # 타임아웃 등으로 스레드가 응답을 주지 않은 경우
            error_msg = f"작업 시간 초과 또는 응답 없음 (제한: {TIMEOUT_SECONDS}초)"
            logger.error(error_msg)
            result_message = {
                "examId": exam_id,
                "videoId": video_id,
                "videoType": "POSE_IMITATION",
                "analyzedAt": datetime.now(KST).isoformat(),
                "status": "FAILED",
                "error": error_msg
            }
            # 좀비 스레드는 남지만, 메인 프로세스는 계속 돔 (메모리 누수 가능성 -> 추후 request count로 해결)

        except Exception as e:
            # 분석 내부 에러 처리
            error_msg = str(e)
            logger.error("examId=%s 실패: %s", exam_id, error_msg)
            result_message = {
                "examId": exam_id,
                "videoId": video_id,
                "videoType": "POSE_IMITATION",
                "analyzedAt": datetime.now(KST).isoformat(),
                "status": "FAILED",
                "error": error_msg
            }

        finally:
            # 임시 파일 정리
            if tmp_path and os.path.exists(tmp_path):
                with contextlib.suppress(Exception):
                    os.remove(tmp_path)

        # 결과 발행 및 Ack
        self.publish_result(result_message)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _load_video(self, task: dict) -> str:
        """비디오 로드 (로컬 경로 또는 S3 Presigned URL)"""
        # 옵션 1: 로컬 경로 (테스트용)
        if "video_path" in task:
            path = task["video_path"]
            if not os.path.exists(path):
                raise ValueError(f"비디오 경로를 찾을 수 없음: {path}")
            logger.info("로컬 비디오 사용: %s", path)
            return path

        # 옵션 2: s3Uri (Presigned URL)
        if "s3Uri" in task:
            logger.info("S3에서 비디오 다운로드 중...")
            response = requests.get(task["s3Uri"], timeout=120)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(response.content)
                logger.info("다운로드 완료: %s", tmp.name)
                return tmp.name

        raise ValueError("비디오 소스가 제공되지 않음 (video_path 또는 s3Uri 필요)")

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
