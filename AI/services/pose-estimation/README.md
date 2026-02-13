# Pose Estimation Service

> **ViTPose 기반 동작 모방 분석 파이프라인**
> 부모의 동작을 아이가 얼마나 잘 따라하는지 정량적으로 분석합니다.

---

## 목차

1. [개요](#1-개요)
2. [기술 스택](#2-기술-스택)
3. [설치 및 환경 설정](#3-설치-및-환경-설정)
4. [환경별 설정 (로컬/배포)](#4-환경별-설정-로컬배포)
5. [실행 방법](#5-실행-방법)
6. [프로젝트 구조](#6-프로젝트-구조)
7. [파이프라인 흐름](#7-파이프라인-흐름)
8. [모듈별 상세 설명](#8-모듈별-상세-설명)
9. [RabbitMQ 연동](#9-rabbitmq-연동)
10. [REST API 명세](#10-rest-api-명세)
11. [지원 동작 및 연령별 설정](#11-지원-동작-및-연령별-설정)
12. [설정 옵션](#12-설정-옵션)
13. [트러블슈팅](#13-트러블슈팅)

---

## 1. 개요

### 1.1 서비스 목적

- **영상 입력** → **부모/아이 자세 추출** → **동작 유사도 분석** → **결과 반환**
- 아이의 동작 모방 능력을 정량적 수치로 제공
- ADOS(자폐증 진단 관찰 스케줄) 평가 항목 자동 산출

### 1.2 핵심 기능

| 기능 | 설명 |
|------|------|
| 부모-아이 역할 자동 식별 | 몸통(torso) 크기 비교로 자동 구분 |
| 6가지 동작 유형 지원 | 만세, 박수, 점프, 발차기, 던지기, 뒤로걷기 |
| 반응 지연 시간 측정 | 부모 동작 시작 → 아이 동작 시작 시간차 |
| 프레임별 유사도 계산 | DTW 정렬 + 유클리드 거리 기반 |
| ADOS 점수 자동 산출 | B6(기쁨), A8(주의), B18(사회적 모방) |
| 스켈레톤 시각화 | 부모=파란색, 아이=주황색 |

---

## 2. 기술 스택

| 분류 | 기술 | 비고 |
|------|------|------|
| Pose Estimation | ViTPose-Base | `usyd-community/vitpose-base-simple` |
| Person Detection | RT-DETR | `PekingU/rtdetr_r50vd_coco_o365` |
| DTW 정렬 | dtw-python | C-accelerated |
| 표정 분석 | RetinaFace + hsemotion | ADOS B6용 (선택적) |
| Backend | FastAPI, RabbitMQ | REST API + 메시지 큐 |
| 영상 처리 | OpenCV, Pillow | 프레임 추출 및 시각화 |
| Deep Learning | PyTorch 2.5 | CUDA/CPU 지원 |

---

## 3. 설치 및 환경 설정

### 3.1 Conda 환경 생성

```bash
conda create -n pose-worker python=3.11 -y
conda activate pose-worker
```

### 3.2 의존성 설치

```bash
# CPU 환경
pip install -r requirements-cpu.txt

# GPU 환경 (권장)
pip install -r requirements-gpu.txt
```

### 3.3 GPU 지원 (CUDA 12.x)

```bash
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

### 3.4 HuggingFace 토큰 설정 (필수)

ViTPose 및 RT-DETR 모델 다운로드를 위해 HuggingFace 토큰이 필요합니다.

**1. 토큰 발급:**
1. [HuggingFace](https://huggingface.co/) 회원가입
2. [Settings > Access Tokens](https://huggingface.co/settings/tokens) 접속
3. `New token` 클릭 → 이름 입력 → `Read` 권한 선택 → 생성
4. 생성된 토큰 복사

**2. 토큰 설정:**
```bash
# 방법 1: 환경 변수로 설정
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx

# 방법 2: .env 파일에 추가
echo "HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx" >> .env

# 방법 3: huggingface-cli 로그인
pip install huggingface_hub
huggingface-cli login
```

---

## 4. 환경별 설정 (로컬/배포)

### 4.1 파일 구조

로컬 개발과 배포 환경을 분리하기 위해 다음 파일들이 제공됩니다:

```
pose-estimation/
├── .env                    # 현재 사용 중인 환경 변수 (git ignore)
├── .env.local              # 로컬 개발용 (GPU)
├── .env.prod               # 배포용 (CPU, EC2)
├── requirements-cpu.txt    # CPU 환경 의존성
├── requirements-gpu.txt    # GPU 환경 의존성
├── Dockerfile-cpu          # CPU 컨테이너 빌드
├── Dockerfile-gpu          # GPU 컨테이너 빌드
├── docker-compose-cpu.yml  # CPU Docker Compose
└── docker-compose-gpu.yml  # GPU Docker Compose
```

### 4.2 환경별 차이점

| 항목 | 로컬 (.env.local) | 배포 (.env.prod) |
|------|-------------------|------------------|
| **DEVICE** | `cuda` (GPU) | `cpu` |
| **DEBUG_MODE** | `true` | `false` |
| **LOG_LEVEL** | `DEBUG` | `INFO` |
| **RABBITMQ_HOST** | `localhost` | `rabbitmq` (Docker 내부) |
| **TASK_QUEUE** | `pose_task_queue` | `analysis.req.task1` |
| **RESULT_QUEUE** | `pose_result_queue` | `analysis.resp` |

### 4.3 환경 설정 방법

**로컬 개발 (GPU):**
```bash
# .env.local을 .env로 복사
cp .env.local .env

# HuggingFace 토큰 추가
echo "HF_TOKEN=hf_xxxxxxxx" >> .env

# GPU Docker Compose 사용
docker-compose -f docker-compose-gpu.yml up -d
```

**배포 환경 (CPU, EC2):**
```bash
# .env.prod를 .env로 복사
cp .env.prod .env

# HuggingFace 토큰 추가
echo "HF_TOKEN=hf_xxxxxxxx" >> .env

# CPU Docker Compose 사용
docker-compose -f docker-compose-cpu.yml up -d
```

### 4.4 의존성 파일 선택

| 환경 | requirements 파일 | Dockerfile | docker-compose |
|------|------------------|------------|----------------|
| 로컬 GPU | `requirements-gpu.txt` | `Dockerfile-gpu` | `docker-compose-gpu.yml` |
| 배포 CPU | `requirements-cpu.txt` | `Dockerfile-cpu` | `docker-compose-cpu.yml` |

**차이점:**
- `requirements-gpu.txt`: PyTorch CUDA 버전 포함
- `requirements-cpu.txt`: PyTorch CPU 버전 (경량)

### 4.5 .env 파일 예시

```bash
# =============================================================================
# 필수 설정
# =============================================================================
DEVICE=cuda                    # cuda | cpu | mps
HF_TOKEN=hf_xxxxxxxxxxxxxxxx   # HuggingFace 토큰 (필수!)

# =============================================================================
# 서버 설정
# =============================================================================
APP_NAME=ViTPose Motion Analyzer
DEBUG_MODE=true
LOG_LEVEL=DEBUG

# =============================================================================
# RabbitMQ 설정
# =============================================================================
RABBITMQ_HOST=localhost        # Docker 내부: rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
TASK_QUEUE=analysis.req.task1
RESULT_QUEUE=analysis.resp

# =============================================================================
# 모델 설정 (HuggingFace)
# =============================================================================
PERSON_DETECTOR=PekingU/rtdetr_r50vd_coco_o365
POSE_MODEL=usyd-community/vitpose-base-simple

# =============================================================================
# 영상 처리
# =============================================================================
TARGET_FPS=10.0
MAX_VIDEO_FRAMES=300
MAX_VIDEO_DURATION_SEC=30.0

# =============================================================================
# 동작 임계값
# =============================================================================
THRESHOLD_CLAPPING=0.6
THRESHOLD_HURRAY=0.6
THRESHOLD_WALKING_BACK=0.6
THRESHOLD_JUMPING=0.6
THRESHOLD_KICKING=0.6
THRESHOLD_THROWING=0.6
```

---

## 5. 실행 방법

### 5.1 Docker 실행 (권장)

```bash
# GPU 환경 - 전체 서비스 실행
docker-compose -f docker-compose-gpu.yml up -d

# CPU 환경
docker-compose -f docker-compose-cpu.yml up -d

# Worker만 실행 (외부 RabbitMQ 사용시)
docker-compose -f docker-compose-gpu.yml up -d pose-worker

# 로그 확인
docker-compose logs -f pose-worker
```

### 5.2 CLI 분석

```bash
# 기본 사용법
python -m app.pipeline.analyzer <영상경로> <동작유형> --age <월령>

# 예시: 만세 동작 분석
python -m app.pipeline.analyzer video.mp4 hurray --age 18

# 시각화 포함
python -m app.pipeline.analyzer video.mp4 hurray --age 18 --visualize

# 상세 로그
python -m app.pipeline.analyzer video.mp4 hurray --age 18 --verbose
```

**CLI 옵션:**

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--age`, `-a` | 아동 월령 (12-24) | 18 |
| `--visualize`, `-v` | 시각화 활성화 | False |
| `--output`, `-o` | 시각화 출력 폴더 | `analysis_output` |
| `--no-video` | 스켈레톤 동영상 생성 안함 | False |
| `--no-smooth` | 스무딩 비활성화 | False |
| `--smooth-method` | 스무딩 방법 | `one_euro` |
| `--verbose` | 상세 로그 | False |

### 5.3 FastAPI 서버 실행

```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
python -m app.main
```

- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 5.4 RabbitMQ Worker 실행

```bash
python -m app.worker
```

---

## 6. 프로젝트 구조

```
pose-estimation/
├── app/
│   ├── __init__.py
│   ├── config.py                 # 환경 설정 (pydantic-settings)
│   ├── main.py                   # FastAPI REST 서버
│   ├── worker.py                 # RabbitMQ 워커
│   ├── models/
│   │   └── vitpose.py            # ViTPose + RT-DETR 래퍼 (Singleton)
│   ├── pipeline/
│   │   ├── analyzer.py           # MotionAnalyzer (핵심 오케스트레이터)
│   │   ├── video_processor.py    # 영상 → 프레임 추출
│   │   ├── pose_extractor.py     # 프레임 → 17 keypoints
│   │   ├── normalizer.py         # 정규화 + 역할 식별 + 스무딩
│   │   ├── dtw.py                # Dynamic Time Warping 정렬
│   │   ├── similarity.py         # 유사도 계산
│   │   ├── exceptions.py         # 커스텀 예외 클래스
│   │   └── emotion/              # 표정 분석 모듈
│   │       ├── expression_analyzer.py
│   │       ├── face_detector.py
│   │       └── emotion_recognizer.py
│   └── utils/
│       └── visualize.py          # 스켈레톤 시각화
├── tests/                        # 테스트 코드
├── docs/                         # 개발 문서
├── docker-compose-gpu.yml        # GPU Docker Compose
├── docker-compose-cpu.yml        # CPU Docker Compose
├── requirements-gpu.txt          # GPU 의존성
├── requirements-cpu.txt          # CPU 의존성
└── README.md
```

---

## 7. 파이프라인 흐름

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VIDEO INPUT (S3 URL / Local)                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  VideoProcessor │ 프레임 추출 (10fps 리샘플링, 최대 30초/300프레임)          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PoseExtractor  │ RT-DETR (사람 검출) + ViTPose (17 COCO keypoints)      │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PoseNormalizer │ 역할 식별 (torso 길이 비교: 큰쪽=부모, 작은쪽=아동)         │
│                 │ 정규화 (torso/bbox/hip_center)                         │
│                 │ 스무딩 (one_euro/moving_avg/exponential/gaussian)      │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ ReactionDelay   │ 동작별 시작 프레임 탐지                                  │
│ Calculation     │ hurray: 손목 > 어깨+margin                             │
│                 │ clapping: 양손목 거리 < threshold                      │
│                 │ jumping: 엉덩이 y좌표 상승                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  DTWAligner     │ Dynamic Time Warping으로 부모-아동 시퀀스 정렬            │
│                 │ Sakoe-Chiba window constraint (효율성)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ SimilarityCalc  │ similarity = 1 / (1 + euclidean_distance)             │
│                 │ 동작별 가중치 적용 (상체/하체/머리)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  MotionAnalyzer │ 임계치 비교 → Pass/Fail 판정                            │
│ (Orchestrator)  │ ADOS 점수 산출: B6(기쁨), A8(주의), B18(사회적 모방)      │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   RabbitMQ / REST API OUTPUT                            │
│  { examId, metrics: {per_trial}, ADOS: {B6, A8, B18} }                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 단계별 요약

| 단계 | 모듈 | 입력 | 출력 |
|:---:|------|------|------|
| 1 | VideoProcessor | 영상 파일 | 프레임 이미지 (10fps) |
| 2 | PoseExtractor | 프레임 | 17개 관절 좌표 |
| 3 | PoseNormalizer | 관절 좌표 | 정규화된 부모/아이 시퀀스 |
| 4 | ReactionDelay | 시퀀스 | 동작 시작 시점 |
| 5 | DTWAligner | query, ref | 정렬된 시퀀스 쌍 |
| 6 | SimilarityCalculator | 정렬된 쌍 | 유사도 점수 |
| 7 | MotionAnalyzer | 모든 메트릭 | AnalysisResult |

---

## 8. 모듈별 상세 설명

### 8.1 VideoProcessor

**역할:** 영상 파일을 프레임으로 분해

```python
extract_frames(video_path)           # Generator 방식 (메모리 효율)
extract_frames_to_folder(video_path) # 폴더 저장 방식
get_video_info(video_path)           # 영상 메타데이터
```

**설정:**
- `TARGET_FPS`: 10 (기본)
- `MAX_VIDEO_FRAMES`: 300
- `MAX_VIDEO_DURATION_SEC`: 30초

### 8.2 PoseExtractor

**역할:** 프레임에서 2D 관절 좌표 추출

**COCO 17 Keypoints:**
```
0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear,
5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow,
9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip,
13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle
```

### 8.3 PoseNormalizer

**역할:** 정규화, 역할 식별, 스무딩

**역할 식별 로직:**
- 몸통 길이(어깨-골반 거리) 비교
- 큰 쪽 → 부모, 작은 쪽 → 아이

**정규화 방식:**
- 몸통 중심 기준 좌표 변환
- 몸통 길이 기준 스케일 정규화

**스무딩 방법:**
- `one_euro`: 1€ 필터 (기본, 권장)
- `moving_avg`: 단순 이동 평균
- `exponential`: 지수 이동 평균
- `gaussian`: 가우시안 필터

### 8.4 DTWAligner

**역할:** Dynamic Time Warping으로 시간축 정렬

- 라이브러리: `dtw-python` (C-accelerated)
- Sakoe-Chiba 밴드로 정렬 경로 제약

### 8.5 SimilarityCalculator

**역할:** 정렬된 시퀀스 간 유사도 계산

**공식:**
```
similarity = 1 / (1 + euclidean_distance)
```

**동작별 가중치:**

| 동작 | 상체 | 하체 | 머리 |
|------|:----:|:----:|:----:|
| hurray | 2.0 | 0.5 | 0.3 |
| clapping | 2.5 | 0.3 | 0.2 |
| jumping | 1.0 | 2.0 | 0.5 |
| kicking | 1.0 | 2.0 | 0.3 |
| throwing | 2.0 | 0.5 | 0.3 |
| walking_back | 1.0 | 1.5 | 0.3 |

---

## 9. RabbitMQ 연동

### 9.1 큐 설정

| 큐 | 방향 | 용도 |
|----|------|------|
| `analysis.req.task1` | BE → AI | 분석 요청 수신 |
| `analysis.resp` | AI → BE | 분석 결과 발행 |

### 9.2 입력 메시지 (BE → AI)

```json
{
  "examId": "uuid-1234",
  "videoId": "uuid-5678",
  "videoType": "POSE_IMITATION",
  "childName": "홍길동",
  "ageMonths": 18,
  "s3Uri": "https://s3.../video.mp4"
}
```

### 9.3 출력 메시지 (AI → BE)

```json
{
  "examId": "uuid-1234",
  "videoId": "uuid-5678",
  "videoType": "POSE_IMITATION",
  "analyzedAt": "2026-02-09T10:30:00+09:00",
  "status": "SUCCESS",
  "metrics": {
    "per_trial": [
      {
        "trial_index": 1,
        "action_type": "clapping",
        "success": true,
        "similarity_score": 0.8532,
        "parent_start_time": 0.0,
        "parent_end_time": 3.0,
        "child_start_time": 4.25,
        "child_end_time": 7.75,
        "latency_s": 1.25,
        "duration_s": 3.50,
        "attention_ratio": 0.9234
      },
      {
        "trial_index": 2,
        "action_type": "hurray",
        "success": true,
        "similarity_score": 0.7821,
        "parent_start_time": 10.0,
        "parent_end_time": 13.0,
        "child_start_time": 14.50,
        "child_end_time": 17.80,
        "latency_s": 1.50,
        "duration_s": 3.30,
        "attention_ratio": 0.8745
      },
      {
        "trial_index": 3,
        "action_type": "walking_back",
        "success": false,
        "similarity_score": 0.4523,
        "parent_start_time": 20.0,
        "parent_end_time": 23.0,
        "child_start_time": null,
        "child_end_time": null,
        "latency_s": null,
        "duration_s": null,
        "attention_ratio": 0.3421
      }
    ]
  },
  "ADOS": {
    "B6": true,
    "A8": 1,
    "B18": true
  }
}
```

### 9.4 ADOS 점수 설명

| 항목 | 타입 | 설명 |
|------|------|------|
| B6 | boolean | 기쁨/즐거움 표현 감지 여부 |
| A8 | 0-3 | 주의/반응 수준 (0=정상, 3=심각) |
| B18 | boolean | 사회적 모방 성공 여부 |

---

## 10. REST API 명세

### 10.1 헬스 체크

```http
GET /health
```

**응답:**
```json
{
  "status": "healthy",
  "device": "cuda",
  "debug_mode": false,
  "analyzer_ready": true
}
```

### 10.2 단일 동작 분석

```http
POST /api/v1/motion/analyze
Content-Type: multipart/form-data
```

**파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| video | file | O | 영상 파일 |
| action_type | string | O | 동작 유형 |
| age_months | int | O | 아동 월령 |
| response_type | string | X | json / video / full |

**응답:**
```json
{
  "passed": true,
  "similarity_score": 0.8234,
  "reaction_delay_sec": 0.72,
  "duration_sec": 2.3,
  "validity": 0.95,
  "threshold_used": 0.65,
  "action_type": "hurray",
  "age_months": 18,
  "processing_time_sec": 4.52,
  "role_info": {
    "parent_identified": true,
    "child_identified": true,
    "parent_torso_length": 156.2,
    "child_torso_length": 89.4
  },
  "details": {
    "upper_body_score": 0.88,
    "lower_body_score": 0.76,
    "head_score": 0.82,
    "total_frames_analyzed": 45
  }
}
```

### 10.3 다중 동작 분석 (3-trial)

```http
POST /api/v1/motion/analyze-multi-trial
Content-Type: multipart/form-data
```

**파라미터:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|:----:|------|
| video | file | O | 영상 파일 |
| actions | string | O | JSON 배열 (3개 동작) |
| age_months | int | O | 아동 월령 |

### 10.4 에러 응답

```json
{
  "error_code": "PARENT_NOT_DETECTED",
  "message": "부모 시퀀스를 감지하지 못했습니다.",
  "details": {
    "video_path": "video.mp4"
  }
}
```

**에러 코드:**

| 코드 | 설명 |
|------|------|
| PARENT_NOT_DETECTED | 부모 미감지 |
| CHILD_NOT_DETECTED | 아이 미감지 |
| VIDEO_PROCESSING_ERROR | 영상 파일 문제 |
| POSE_EXTRACTION_ERROR | 관절 추출 실패 |

---

## 11. 지원 동작 및 연령별 설정

### 11.1 연령별 동작 세트

| 연령대 | 동작 1 | 동작 2 | 동작 3 |
|--------|--------|--------|--------|
| 12-17개월 | clapping | hurray | walking_back |
| 18-24개월 | jumping | kicking | throwing |

### 11.2 동작별 상세

| 동작 | 영문 | 설명 | 검출 방식 |
|------|------|------|----------|
| 만세 | hurray | 양팔을 머리 위로 올림 | 양쪽 손목 > 어깨 + margin |
| 박수 | clapping | 양손을 마주침 | 양손목 거리 < threshold |
| 점프 | jumping | 제자리에서 뛰어오름 | 엉덩이 y좌표 상승 |
| 발차기 | kicking | 한 발로 공 차는 동작 | 좌우 발목 높이 차 |
| 던지기 | throwing | 공을 던지는 동작 | 한쪽 손목 > 어깨 |
| 뒤로걷기 | walking_back | 뒤로 걸어감 | 골반 x좌표 이동 |

### 11.3 촬영 가이드

**권장 사항:**
- 부모와 아이가 함께 촬영
- 전신이 보이도록 촬영 (발끝~머리)
- 정면 또는 측면 촬영
- 5-10초 분량

**주의 사항:**
- 너무 가까이에서 촬영 시 관절 감지 실패
- 부모/아이 중 한 명만 있으면 에러

---

## 12. 설정 옵션

### 12.1 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| DEVICE | 연산 장치 (cuda/cpu/mps) | cuda |
| LOG_LEVEL | 로그 레벨 | INFO |
| DEBUG_MODE | 디버그 모드 | false |
| TARGET_FPS | 프레임 추출 FPS | 10.0 |
| MAX_VIDEO_DURATION_SEC | 최대 영상 길이 | 30.0 |
| RABBITMQ_HOST | RabbitMQ 호스트 | localhost |
| RABBITMQ_PORT | RabbitMQ 포트 | 5672 |

### 12.2 동작별 판정 임계값

| 동작 | 임계값 | 설정 변수 |
|------|:------:|----------|
| clapping | 0.60 | THRESHOLD_CLAPPING |
| hurray | 0.60 | THRESHOLD_HURRAY |
| walking_back | 0.60 | THRESHOLD_WALKING_BACK |
| jumping | 0.60 | THRESHOLD_JUMPING |
| kicking | 0.60 | THRESHOLD_KICKING |
| throwing | 0.60 | THRESHOLD_THROWING |

---

## 13. 트러블슈팅

### 13.1 CUDA 관련

```bash
# CUDA 버전 확인
nvidia-smi

# PyTorch CUDA 확인
python -c "import torch; print(torch.cuda.is_available())"
```

### 13.2 모델 다운로드 실패

```bash
# HuggingFace 캐시 초기화
rm -rf ~/.cache/huggingface/hub

# 수동 다운로드
python -c "from transformers import AutoModel; AutoModel.from_pretrained('usyd-community/vitpose-base-simple')"
```

### 13.3 에러 코드별 대응

| 에러 코드 | 원인 | 해결 방법 |
|----------|------|----------|
| PARENT_NOT_DETECTED | 부모 미감지 | 부모와 아이 함께 촬영 |
| CHILD_NOT_DETECTED | 아이 미감지 | 부모와 아이 함께 촬영 |
| VIDEO_PROCESSING_ERROR | 영상 파일 문제 | 지원 포맷 확인 (mp4, webm, avi, mov) |
| POSE_EXTRACTION_ERROR | 관절 추출 실패 | 전신이 보이도록 재촬영 |

### 13.4 성능 최적화

- **GPU 사용**: CPU 대비 10배 이상 빠름
- **FPS 조절**: 빠른 동작이 아니면 5fps로도 충분
- **영상 길이**: 30초 이하 권장

---

*Last Updated: 2026-02-09*
