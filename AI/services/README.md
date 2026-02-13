# AI Services

ADOS-2 검사 항목별 독립 분석 서비스 모음입니다. 각 서비스는 RabbitMQ를 통해 비동기로 작업을 처리합니다.

---

## 서비스 개요

| 서비스 | Task | 검사 항목 | 입력 큐 | 상태 |
|--------|------|----------|---------|------|
| [pose-estimation](#1-pose-estimation-동작-모방) | Task 1 | 동작 모방 | `analysis.req.task1` | Production |
| [speech-imitation](#2-speech-imitation-발화-모방) | Task 2 | 발화 모방 | `analysis.req.task2` | Production |
| [face-to-face-name-response](#3-face-to-face-name-response-대면-호명) | Task 3 | 대면 호명반응 | `analysis.req.task3` | Production |
| [name_non_facing](#4-name_non_facing-비대면-호명) | Task 4 | 비대면 호명반응 | `analysis.req.task4` | Production |
| [screening](#5-screening-선별-검사) | - | 선별 검사 | - | Development |

**공통 출력 큐**: `analysis.resp`

---

## 아키텍처

```
                              RabbitMQ
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ analysis.req. │      │ analysis.req. │      │ analysis.req. │
│    task1      │      │    task2      │      │   task3/4     │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│    pose-      │      │   speech-     │      │ name_non_     │
│  estimation   │      │  imitation    │      │   facing      │
│               │      │               │      │               │
│ ┌───────────┐ │      │ ┌───────────┐ │      │ ┌───────────┐ │
│ │ ViTPose   │ │      │ │ Whisper   │ │      │ │ YOLO Head │ │
│ │ RT-DETR   │ │      │ │ Silero    │ │      │ │ 6DRepNet  │ │
│ │ DTW       │ │      │ │ MFCC+DTW  │ │      │ │ Whisper   │ │
│ │ hsemotion │ │      │ │ Pitch     │ │      │ │ pyannote  │ │
│ └───────────┘ │      │ └───────────┘ │      │ └───────────┘ │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        └──────────────────────┴──────────────────────┘
                               │
                               ▼
                      ┌───────────────┐
                      │ analysis.resp │
                      └───────────────┘
```

---

## 1. pose-estimation (동작 모방)

부모의 동작을 아이가 얼마나 잘 따라하는지 정량적으로 분석합니다.

### 기술 스택

| 모델 | 용도 |
|------|------|
| **RT-DETR** (PekingU/rtdetr_r50vd_coco_o365) | 사람 감지 |
| **ViTPose-Base** (usyd-community/vitpose-base-simple) | 자세 추정 (17 keypoints) |
| **DTW** (Dynamic Time Warping) | 시간축 정렬 |
| **RetinaFace + hsemotion** | 표정 분석 (ADOS B6) |

### 분석 동작 (월령별)

| 월령 | 동작 세트 |
|------|----------|
| 12-17개월 | clapping, hurray, walking_back |
| 18-24개월 | jumping, kicking, throwing |

### 주요 설정

```bash
# 모델
PERSON_DETECTOR=PekingU/rtdetr_r50vd_coco_o365
POSE_MODEL=usyd-community/vitpose-base-simple
DEVICE=cuda  # or cpu

# 분석
TARGET_FPS=10.0
DTW_DISTANCE_METRIC=euclidean
DTW_WINDOW_RATIO=0.1

# 동작별 임계값
THRESHOLD_CLAPPING=0.6
THRESHOLD_HURRAY=0.6
THRESHOLD_JUMPING=0.6
```

### ADOS 점수

| 항목 | 기준 |
|------|------|
| **B6** | 기쁨 표정 비율 >= 10% → `true` |
| **A8** | 평균 유사도 기반 → 0-3점 |
| **B18** | 주의 집중 → `true/false` |

### 실행

```bash
cd AI/services/pose-estimation

# Docker (권장)
docker-compose -f docker-compose-cpu.yml up -d

# 로컬
cp .env.local .env
python -m app.worker
```

---

## 2. speech-imitation (발화 모방)

부모의 발화를 아이가 얼마나 비슷하게 따라하는지 분석합니다.

### 기술 스택

| 모델/기법 | 용도 |
|----------|------|
| **Silero VAD** | 음성 활동 감지 |
| **Pitch Analysis** (librosa) | 화자 분리 (엄마/아기) |
| **MFCC + DTW** | 발화 유사도 계산 |

### 자극어 (월령별)

| 월령 | 자극 목록 |
|------|----------|
| 12-17개월 | 아, 마, 바, 맘마, 까꿍 |
| 18-23개월 | 엄마, 우유, 자동차, 까까 주세요, 야호! |

### 주요 설정

```bash
# 오디오
SAMPLE_RATE=16000
VAD_THRESHOLD=0.3

# 화자 분리
PITCH_CHILD_HZ_THRESHOLD=200.0  # 이상이면 아기로 간주

# 유사도
N_MFCC=13
DTW_RADIUS=20
SIMILARITY_THRESHOLD=0.29

# 타이밍
STIMULUS_MAX_SEC=2.0
RESPONSE_TIMEOUT_SEC=5.0
```

### 분석 흐름

```
Audio → VAD → Pitch-based Speaker Separation → MFCC Extraction → DTW Similarity
```

### 실행

```bash
cd AI/services/speech-imitation

# Docker
docker-compose up -d

# 로컬
python -m app.worker
```

---

## 3. face-to-face-name-response (대면 호명)

대면 상황에서 이름을 불렀을 때 아이의 반응을 분석합니다.

### 기술 스택

| 모델 | 용도 |
|------|------|
| **Whisper** | 호명 탐지 (STT) |
| **Face Detection** | 얼굴 감지 |
| **Gaze Analysis** | 시선 추적 |

### 실행

```bash
cd AI/services/face-to-face-name-response
docker-compose up -d
```

---

## 4. name_non_facing (비대면 호명)

아이가 뒤돌아 있는 상황에서 이름을 불렀을 때의 반응(시선 전환, 음성)을 분석합니다.

### 기술 스택

| 모델 | 용도 |
|------|------|
| **YOLO Head** (yolo_p2layer_jh.pt) | 머리 감지 (뒤통수 포함) |
| **6DRepNet360** | 360° 머리 포즈 추정 |
| **faster-whisper** (large-v3-turbo) | STT (한국어) |
| **pyannote-audio** (3.1) | 화자 분리 |
| **Silero VAD** | 음성 활동 감지 |

### 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Stages                          │
├─────────────────────────────────────────────────────────────┤
│  InputStage → TriggerStage → ReactionStage → ResultStage   │
│      │             │               │              │         │
│  비디오/오디오   호명 탐지      시선/음성 반응    ADOS 점수  │
│    추출        (Whisper)        분석            산출        │
└─────────────────────────────────────────────────────────────┘
```

### 반응 판정 모드

| 모드 | 설명 |
|------|------|
| `gaze_only` | 시선 전환만 판정 |
| `voice_only` | 음성 반응만 판정 |
| `or` | 시선 OR 음성 (기본값) |
| `and` | 시선 AND 음성 |
| `weighted` | 가중 합산 |

### 주요 설정

```bash
# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_HEARTBEAT=600
INPUT_QUEUE=analysis.req.task4
OUTPUT_QUEUE=analysis.resp

# Vision
YOLO_HEAD_CONFIDENCE=0.15
GAZE_ANGLE_THRESHOLD_DEG=20.0
MIN_GAZE_DURATION_SEC=0.5

# Audio
WHISPER_MODEL_SIZE=large-v3-turbo
WHISPER_LANGUAGE=ko
DIARIZATION_MAX_SPEAKERS=2

# 반응 판정
REACTION_MODE=or
REACTION_TIMEOUT_SEC=5.0
```

### ADOS 점수

| 항목 | 기준 |
|------|------|
| **B7** | 3회 중 반응 횟수 → 0-3점 |
| **B18** | 평균 반응 시간 < 3초 → `true` |

### Smoothing (떨림 방지)

```bash
ENABLE_SMOOTHING=true
SMOOTHING_ALPHA_POSE=0.3   # Head pose
SMOOTHING_ALPHA_GAZE=0.4   # Gaze direction
SMOOTHING_ALPHA_BBOX=0.5   # Bounding box
```

### 실행

```bash
cd AI/services/name_non_facing

# Docker CPU
docker-compose -f docker-compose-cpu.yml up -d

# Docker GPU
docker-compose -f docker-compose-gpu.yml up -d

# 로컬
cp .env.local .env
python -m app.worker
```

---

## 5. screening (선별 검사)

간이 선별 검사를 위한 보조 서비스입니다.

### 실행

```bash
cd AI/services/screening
docker-compose up -d
```

---

## 공통 메시지 형식

### Request (BE → AI)

```json
{
  "examId": "UUID",
  "videoId": "UUID",
  "videoType": "POSE_IMITATION | SPEECH_IMITATION | NAME_FACING | NAME_NON_FACING",
  "childName": "아이이름",
  "ageMonths": 18,
  "s3Uri": "s3://bucket/path/video.mp4"
}
```

### Response (AI → BE)

```json
{
  "examId": "UUID",
  "videoId": "UUID",
  "videoType": "POSE_IMITATION",
  "analyzedAt": "2025-02-13T15:30:00+09:00",
  "status": "SUCCESS | FAILED",
  "metrics": {
    "per_trial": [...]
  },
  "ADOS": {
    "B6": true,
    "A8": 0,
    "B7": 1,
    "B18": true
  },
  "errorMessage": null
}
```

---

## Worker 패턴

모든 서비스는 **Threaded Worker Pattern**을 사용하여 장시간 분석 중에도 RabbitMQ 연결을 유지합니다.

```python
def process_message(self, ch, method, properties, body):
    # 1. 분석 스레드 생성
    worker_thread = threading.Thread(target=run_pipeline)
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

## 환경 분리

### CPU vs GPU

| 환경 | 파일 | DEVICE | 용도 |
|------|------|--------|------|
| 로컬 GPU | `.env.local`, `docker-compose-gpu.yml` | `cuda` | 빠른 개발/테스트 |
| 배포 CPU | `.env.prod`, `docker-compose-cpu.yml` | `cpu` | AWS EC2 배포 |

### 환경 변수 예시

```bash
# .env.local (GPU)
DEVICE=cuda
WHISPER_DEVICE=cuda
DIARIZATION_DEVICE=cuda
RABBITMQ_HOST=localhost

# .env.prod (CPU)
DEVICE=cpu
WHISPER_DEVICE=cpu
DIARIZATION_DEVICE=cpu
RABBITMQ_HOST=rabbitmq
```

---

## 디렉토리 구조

```
services/
├── pose-estimation/
│   ├── app/
│   │   ├── main.py              # FastAPI
│   │   ├── worker.py            # RabbitMQ Consumer
│   │   ├── config.py            # 설정
│   │   ├── models/              # ML 모델
│   │   └── pipeline/            # 분석 파이프라인
│   ├── docker-compose-cpu.yml
│   ├── docker-compose-gpu.yml
│   ├── requirements-cpu.txt
│   ├── requirements-gpu.txt
│   └── README.md
│
├── speech-imitation/
│   ├── app/
│   │   ├── worker.py
│   │   ├── config.py
│   │   └── ...
│   ├── docker-compose.yml
│   └── README.md
│
├── face-to-face-name-response/
│   ├── app/
│   ├── docker-compose.yml
│   └── README.md
│
├── name_non_facing/
│   ├── app/
│   │   ├── main.py
│   │   ├── worker.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── yolo_head.py
│   │   │   ├── sixdrepnet.py
│   │   │   └── whisper_model.py
│   │   ├── pipeline/
│   │   │   ├── orchestrator.py
│   │   │   ├── context.py
│   │   │   └── stages/
│   │   ├── core/
│   │   └── services/
│   ├── docker-compose-cpu.yml
│   ├── docker-compose-gpu.yml
│   └── README.md
│
├── screening/
│   ├── app/
│   ├── docker-compose.yml
│   └── README.md
│
└── README.md  (이 파일)
```

---

## 전체 서비스 실행

### Docker Compose로 전체 실행

```bash
# 각 서비스 디렉토리에서 개별 실행
cd AI/services/pose-estimation && docker-compose -f docker-compose-cpu.yml up -d
cd AI/services/speech-imitation && docker-compose up -d
cd AI/services/face-to-face-name-response && docker-compose up -d
cd AI/services/name_non_facing && docker-compose -f docker-compose-cpu.yml up -d
```

### 상태 확인

```bash
# 각 서비스 Health Check
curl http://localhost:8001/health  # pose-estimation
curl http://localhost:8002/health  # speech-imitation
curl http://localhost:8003/health  # face-to-face
curl http://localhost:8004/health  # name_non_facing

# RabbitMQ Management UI
open http://localhost:15672  # guest/guest
```

---

## 트러블슈팅

### RabbitMQ 연결 끊김

**증상**: 장시간 분석 중 연결 타임아웃

**해결**: Threaded Worker 패턴 적용 + heartbeat 설정
```bash
RABBITMQ_HEARTBEAT=600  # 10분
```

### CUDA Out of Memory

**해결**: CPU 모드로 전환
```bash
DEVICE=cpu
WHISPER_DEVICE=cpu
```

### 모델 로딩 느림

**원인**: 첫 실행 시 HuggingFace 모델 다운로드

**해결**: Docker Volume으로 캐시 유지
```yaml
volumes:
  - huggingface_cache:/root/.cache/huggingface
```

### 뒤통수 미감지

**원인**: 기본 얼굴 감지 모델은 정면만 탐지

**해결**: YOLO Head 커스텀 모델 사용
```bash
YOLO_HEAD_MODEL=models/yolo_p2layer_jh.pt
YOLO_HEAD_CONFIDENCE=0.15  # 낮은 임계값
```
