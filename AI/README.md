# AI - ADOS 자동 분석 시스템

ADOS-2 프로토콜 기반 자폐 스펙트럼 선별 검사를 자동화하는 AI 분석 파이프라인입니다.

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client (Parent App)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Backend (Spring Boot)                              │
│                      S3 업로드 + RabbitMQ 메시지 발행                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Task Queue (RabbitMQ)                             │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │
│   │ analysis.req. │  │ analysis.req. │  │ analysis.req. │  │analysis.req.│ │
│   │    task1      │  │    task2      │  │    task3      │  │   task4     │ │
│   │  (동작모방)    │  │  (발화모방)    │  │ (대면호명)     │  │(비대면호명) │ │
│   └───────┬───────┘  └───────┬───────┘  └───────┬───────┘  └──────┬──────┘ │
└───────────┼──────────────────┼──────────────────┼─────────────────┼────────┘
            │                  │                  │                 │
   ┌────────▼────────┐ ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
   │  Pose Worker    │ │ Speech Worker │ │  Name Worker  │ │  Name Worker  │
   │  (pose-estim.)  │ │ (speech-imit.)│ │ (face-to-face)│ │(name-non-fac.)│
   └────────┬────────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                  │                  │                 │
            └──────────────────┴──────────────────┴─────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Output Queue (analysis.resp)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Backend → DB 저장 → Doctor Dashboard                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 프로젝트 구조

```
AI/
├── services/
│   ├── pose-estimation/              # Task 1: 동작 모방 분석
│   │   ├── app/
│   │   │   ├── main.py               # FastAPI + REST API
│   │   │   ├── worker.py             # RabbitMQ Consumer
│   │   │   ├── config.py             # 환경 설정
│   │   │   ├── models/vitpose.py     # ViTPose 모델
│   │   │   └── pipeline/
│   │   │       ├── analyzer.py       # MotionAnalyzer
│   │   │       ├── dtw.py            # 시간 정렬
│   │   │       └── emotion/          # 표정 분석
│   │   ├── docker-compose-cpu.yml
│   │   └── requirements-cpu.txt
│   │
│   ├── speech-imitation/             # Task 2: 발화 모방 분석
│   │
│   ├── face-to-face-name-response/   # Task 3: 대면 호명반응 분석
│   │
│   └── name_non_facing/              # Task 4: 비대면 호명반응 분석
│       ├── app/
│       │   ├── main.py               # FastAPI Health API
│       │   ├── worker.py             # RabbitMQ Consumer
│       │   ├── config.py             # 환경 설정
│       │   ├── services/rabbitmq.py  # MQ 연결 관리
│       │   ├── models/               # ML 모델
│       │   │   ├── yolo_head.py
│       │   │   ├── sixdrepnet.py
│       │   │   └── whisper_model.py
│       │   ├── pipeline/
│       │   │   ├── orchestrator.py   # 파이프라인 조율
│       │   │   ├── context.py        # 상태 공유
│       │   │   └── stages/           # 처리 단계들
│       │   └── core/                 # 핵심 로직
│       ├── docker-compose-cpu.yml
│       └── requirements-cpu.txt
│
├── dataset/
├── MLflow/
├── video_to_img/
└── README.md
```

---

## 모듈 설계

### 1. Ingest Module (Backend 담당)

| 항목 | 내용                                         |
| ---- | -------------------------------------------- |
| 역할 | 영상 업로드 (S3), 메타데이터 생성, Task 발행 |

**Input (Client → Backend)**

```json
{
  "videoFile": "binary",
  "examId": "UUID",
  "childName": "아이이름",
  "ageMonths": 18,
  "videoType": "POSE_IMITATION"
}
```

**Output (Backend → RabbitMQ)**

```json
{
  "examId": "UUID",
  "videoId": "UUID",
  "videoType": "POSE_IMITATION",
  "childName": "아이이름",
  "ageMonths": 18,
  "s3Uri": "s3://bucket/path/video.mp4"
}
```

---

### 2. Vision Inference - Pose Estimation (Task 1)

| 항목 | 내용                                                         |
| ---- | ------------------------------------------------------------ |
| 역할 | 사람 감지 (RT-DETR), Pose 추출 (ViTPose), 부모/아이 구분, 표정 분석 |
| 모델 | ViTPose-Base, RT-DETR, RetinaFace, hsemotion                 |

**Input**

```json
{
  "examId": "UUID",
  "videoId": "UUID",
  "videoType": "POSE_IMITATION",
  "s3Uri": "s3://bucket/video.mp4",
  "ageMonths": 18
}
```

**Output**

```json
{
  "examId": "UUID",
  "videoId": "UUID",
  "status": "SUCCESS",
  "metrics": {
    "per_trial": [
      {
        "trial_index": 1,
        "action_type": "clapping",
        "similarity_score": 0.85,
        "latency_s": 1.25
      }
    ]
  },
  "ADOS": { "B6": true, "A8": 0, "B18": true }
}
```

---

### 3. Vision Inference - Head/Gaze (Task 3/4)

| 항목 | 내용                                                         |
| ---- | ------------------------------------------------------------ |
| 역할 | 머리 감지 (YOLO Head), 머리 포즈 (6DRepNet360), 시선 방향 계산 |
| 모델 | YOLO Head (커스텀 파인튜닝), 6DRepNet360                     |

**Output (Vision 부분)**

```json
{
  "head_detections": [
    {
      "frame": 30,
      "child_head": { "yaw_deg": -15.3, "pitch_deg": 5.2 },
      "gaze_match": true,
      "gaze_angle_to_parent_deg": 12.5
    }
  ]
}
```

---

### 4. Audio Inference Module

| 항목 | 내용                                                         |
| ---- | ------------------------------------------------------------ |
| 역할 | VAD (Silero), 화자 분리 (pyannote), STT (Whisper), 호명 탐지 |
| 모델 | faster-whisper large-v3, pyannote-audio 3.1, Silero VAD      |

**Output**

```json
{
  "speech_segments": [
    {
      "start_s": 0.0,
      "end_s": 0.84,
      "speaker": "SPEAKER_00",
      "text": "동한아",
      "is_name_call": true
    }
  ],
  "speaker_labels": { "SPEAKER_00": "parent", "SPEAKER_01": "child" }
}
```

---

### 5. Alignment Module

| 항목 | 내용                                                         |
| ---- | ------------------------------------------------------------ |
| 역할 | Vision + Audio 타임스탬프 정렬, 반응 시간 계산, Trial 단위 이벤트 추출 |

**Output**

```json
{
  "per_trial": [
    {
      "trial_index": 1,
      "success": true,
      "latency_s": 0.5,
      "voice_detected": true,
      "gaze_match": false
    }
  ],
  "reaction_time_avg": 0.5
}
```

---

### 6. Scoring Module

| 항목 | 내용                         |
| ---- | ---------------------------- |
| 역할 | ADOS-2 임상 기준 기반 점수화 |

**ADOS 점수 기준**

| 항목 | 검사      | 기준                | 점수    |
| ---- | --------- | ------------------- | ------- |
| B6   | 동작 모방 | 기쁨 표정 >= 10%    | Boolean |
| A8   | 동작 모방 | 평균 유사도 기반    | 0-3점   |
| B7   | 호명 반응 | 3회 중 성공 횟수    | 0-3점   |
| B18  | 공통      | 반응 시간/주의 집중 | Boolean |

---

## 비동기 처리 흐름

```
Backend              RabbitMQ               Worker                Backend
   │                    │                     │                      │
   │ 1. Task 발행 ──────▶│                     │                      │
   │◀─ 202 Accepted ────│                     │                      │
   │                    │ 2. 메시지 소비 ─────▶│                      │
   │                    │                     │ 3. S3 다운로드        │
   │                    │◀── Heartbeat ──────▶│ 4. 분석 처리         │
   │                    │   (10분 간격)        │   (30초~5분)         │
   │                    │                     │ 5. 결과 발행 ─────────▶│
   │                    │ 6. ACK ─────────────│                      │
   │                    │                     │                      │ 7. DB 저장
```

### Threaded Worker Pattern

장시간 AI 분석 중 RabbitMQ 연결 유지를 위해 스레드 기반 처리:

```python
def process_message(self, ch, method, properties, body):
    # 1. 워커 스레드 생성
    worker_thread = threading.Thread(target=run_pipeline, args=(task,))
    worker_thread.start()

    # 2. 메인 스레드: Heartbeat 유지
    while worker_thread.is_alive():
        self.connection.process_data_events(time_limit=1)
        time.sleep(1.0)

    # 3. 결과 발행 및 ACK
    self.publish(OUTPUT_QUEUE, result)
    ch.basic_ack(delivery_tag=method.delivery_tag)
```

---

## 기술 스택

### 인프라

| 계층           | 기술          | 용도              |
| -------------- | ------------- | ----------------- |
| Gateway        | FastAPI       | Health Check API  |
| Message Queue  | RabbitMQ      | 비동기 작업 큐    |
| Object Storage | AWS S3        | 영상 파일 저장    |
| Worker         | Python + pika | RabbitMQ Consumer |

### AI 모델

#### Vision Models

| 모델         | 소스            | 용도                    |
| ------------ | --------------- | ----------------------- |
| YOLO Head    | 커스텀 파인튜닝 | 머리 감지 (뒤통수 포함) |
| 6DRepNet360  | TensorFlow Hub  | 360° 머리 포즈          |
| ViTPose-Base | HuggingFace     | 전신 자세 추정          |
| RT-DETR      | HuggingFace     | 사람 감지               |
| RetinaFace   | serengil        | 얼굴 감지               |
| hsemotion    | 사전학습        | 표정 인식               |

#### Audio Models

| 모델           | 소스           | 용도           |
| -------------- | -------------- | -------------- |
| faster-whisper | large-v3-turbo | STT (한국어)   |
| pyannote-audio | 3.1            | 화자 분리      |
| Silero VAD     | PyTorch Hub    | 음성 활동 감지 |

---

## 설계 트레이드오프

### 1. RabbitMQ vs Redis

**선택: RabbitMQ**

| 측면        | RabbitMQ           | Redis          |
| ----------- | ------------------ | -------------- |
| 메시지 보장 | ACK 기반, 영속성   | 기본 휘발성    |
| 라우팅      | 복잡한 라우팅 지원 | 단순 Pub/Sub   |
| 모니터링    | Management UI 내장 | 별도 도구 필요 |

**이유**: AI 분석은 비용이 크므로 메시지 유실 방지 필수

---

### 2. YOLO Head vs MediaPipe Face

**선택: YOLO Head (커스텀 파인튜닝)**

| 측면        | YOLO Head | MediaPipe |
| ----------- | --------- | --------- |
| 뒤통수 감지 | 가능      | 불가      |
| 다양한 각도 | 360°      | 정면 위주 |

**이유**: 비대면 호명 검사에서 아이가 뒤돌아 있는 상황 감지 필수

---

### 3. DTW (Dynamic Time Warping)

**왜 DTW인가?**

```
부모: [●●●●●●] (2초)
아이: [●●●●●●●●●●] (3.5초)
→ 길이가 다른 동작 시퀀스 비교 필요
```

- 시간 길이 정규화
- 속도 차이 보정
- 유클리드 거리 기반 직관적 해석

---

### 4. CPU vs GPU 환경 분리

| 환경       | 디바이스   | 용도        |
| ---------- | ---------- | ----------- |
| 로컬 개발  | GPU (CUDA) | 빠른 테스트 |
| 배포 (AWS) | CPU        | 비용 효율적 |

```bash
# GPU 환경 (로컬)
DEVICE=cuda

# CPU 환경 (배포)
DEVICE=cpu
```

---

## 시작하기

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Mac/Linux

# 패키지 설치
pip install -r requirements.txt
```

### 2. Docker로 실행 (권장)

```bash
# 서비스 디렉토리로 이동
cd AI/services/pose-estimation

# CPU 환경으로 실행
docker-compose -f docker-compose-cpu.yml up -d

# 로그 확인
docker-compose logs -f worker
```

### 3. 로컬 실행

```bash
# 환경 변수 설정
cp .env.local .env

# Worker 실행
python -m app.worker
```

---

## RabbitMQ 설정

| 설정               | 값                   | 설명                |
| ------------------ | -------------------- | ------------------- |
| RABBITMQ_HOST      | localhost / rabbitmq | 호스트              |
| RABBITMQ_PORT      | 5672                 | AMQP 포트           |
| RABBITMQ_HEARTBEAT | 600                  | Heartbeat 간격 (초) |
| PREFETCH_COUNT     | 1                    | 동시 처리 메시지 수 |

## 분석 파라미터

| 설정                     | 값   | 설명                   |
| ------------------------ | ---- | ---------------------- |
| REACTION_TIMEOUT_SEC     | 5.0  | 호명 후 반응 대기 시간 |
| GAZE_ANGLE_THRESHOLD_DEG | 20.0 | 시선 일치 판정 각도    |
| MIN_GAZE_DURATION_SEC    | 0.5  | 최소 응시 지속 시간    |
| DTW_WINDOW_RATIO         | 0.1  | DTW 윈도우 크기 비율   |

---

## API 명세

### Health Check

```
GET /health
Response: { "status": "healthy", "rabbitmq": "connected" }

GET /ready
Response: { "ready": true }
```

### 메시지 큐

**Input Queue (BE → AI)**

```
analysis.req.task1  # 동작 모방
analysis.req.task2  # 발화 모방
analysis.req.task3  # 대면 호명
analysis.req.task4  # 비대면 호명
```

**Output Queue (AI → BE)**

```
analysis.resp  # 공통 응답
```

---

## 핵심 설계 원칙

1. **비동기 분산 처리**: RabbitMQ 기반 메시지 큐로 확장성 확보
2. **모듈화**: 각 검사 유형별 독립 워커, Stage 패턴으로 책임 분리
3. **멀티모달 융합**: Vision + Audio 정보를 타임스탬프 기준 정렬
4. **임상 기준 준수**: ADOS-2 채점 기준을 코드로 구현
5. **환경 분리**: 개발(GPU)과 배포(CPU) 환경 독립적 관리