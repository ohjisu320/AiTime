# Name Non-Facing Service (비대면 호명반응 분석)

> **YOLO Head + 6DRepNet360 기반 시선 분석 파이프라인**
> 아동의 시야 밖에서 호명 시 행동적/음성적 반응을 정량적으로 분석합니다.

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
10. [지표 및 조작적 정의](#10-지표-및-조작적-정의)
11. [설정 옵션](#11-설정-옵션)
12. [트러블슈팅](#12-트러블슈팅)

---

## 1. 개요

### 1.1 서비스 목적

아동의 시야 밖에서 제공된 청각 자극(이름 호명)에 대해, 신체 접촉이나 시각적 단서 없이 **행동적 반응**(고개 및 시선 방향 전환) 또는 **음성적 반응**이 있는지 분석합니다.

- **영상 입력** → **호명 탐지** → **시선/음성 반응 분석** → **ADOS 점수 산출**

### 1.2 핵심 기능

| 기능 | 설명 |
|------|------|
| 호명 자동 탐지 | Whisper로 부모의 호명 시점 (T_start) 감지 |
| 시선 반응 분석 | 6DRepNet360으로 360° 머리 포즈 추정, Gaze Vector 계산 |
| 음성 반응 분석 | VAD + 화자 분리로 아동 음성 반응 탐지 |
| 복합 반응 판정 | OR/AND/가중치 모드 지원 |
| ADOS 점수 산출 | B7(호명반응), B18(사회적 참조) |
| 360° 머리 검출 | YOLO Head로 뒤통수 포함 전방위 검출 |

### 1.3 분석 지표

| 지표 | 설명 |
|------|------|
| Gaze Vector | 머리 방향 벡터 (6DRepNet360 yaw/pitch/roll 기반) |
| Position Vector | 아동 → 부모 방향 벡터 |
| Latency | 호명 종료 ~ 최초 반응 시작 시간 |
| Duration | 부모를 바라보는 시선 유지 시간 |
| Reaction Type | GAZE / VOICE / BOTH / NONE |

---

## 2. 기술 스택

| 분류 | 기술 | 비고 |
|------|------|------|
| 머리 검출 | YOLO Head | `yolo_p2layer_jh.pt` (커스텀 파인튜닝) |
| 머리 포즈 | 6DRepNet360 | 360° yaw/pitch/roll 추정 |
| 음성 인식 | faster-whisper | `large-v3`, 한국어 호명 패턴 매칭 |
| 화자 분리 | pyannote-audio 3.1 | SOTA 화자 분리 |
| VAD | Silero VAD | 30ms 청크 단위 처리 |
| Backend | FastAPI, RabbitMQ | REST API + 메시지 큐 |
| 영상 처리 | OpenCV, FFmpeg | 프레임/오디오 추출 |
| Deep Learning | PyTorch 2.5 | CUDA/CPU 지원 |

---

## 3. 설치 및 환경 설정

### 3.1 Conda 환경 생성

```bash
conda create -n name-worker python=3.11 -y
conda activate name-worker
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

### 3.4 모델 파일 다운로드

YOLO Head 모델 파일이 필요합니다:

**다운로드 링크:**
- [Google Drive - yolo_p2layer_jh.pt](https://drive.google.com/file/d/1PeAzKYBAf5r-btK24KU180nWkMmRHTWN/view?usp=sharing)
  - 크기: 86.4MB
  - 용도: 파인튜닝된 Head Detection 모델

**설치 방법:**
```bash
# 모델 파일을 models/ 디렉토리에 배치
mkdir -p models
# 다운로드 후 models/yolo_p2layer_jh.pt 위치에 저장
```

### 3.5 HuggingFace 토큰 설정 (필수)

pyannote-audio 모델 다운로드를 위해 HuggingFace 토큰이 필요합니다.

**1. 토큰 발급:**
1. [HuggingFace](https://huggingface.co/) 회원가입
2. [Settings > Access Tokens](https://huggingface.co/settings/tokens) 접속
3. `New token` 클릭 → 이름 입력 → `Read` 권한 선택 → 생성
4. 생성된 토큰 복사

**2. pyannote 모델 동의:**
- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) 접속
- "Agree and access repository" 클릭 (라이선스 동의 필요)

**3. 토큰 설정:**
```bash
# 방법 1: 환경 변수로 설정
export DIARIZATION_USE_AUTH_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx

# 방법 2: .env 파일에 추가
echo "DIARIZATION_USE_AUTH_TOKEN=hf_xxxxxxxxxxxxxxxx" >> .env

# 방법 3: huggingface-cli 로그인
pip install huggingface_hub
huggingface-cli login
```

---

## 4. 환경별 설정 (로컬/배포)

### 4.1 파일 구조

```
name_non_facing/
├── .env                    # 현재 사용 중인 환경 변수 (git ignore)
├── .env.local              # 로컬 개발용 (GPU)
├── .env.prod               # 배포용 (CPU, EC2)
├── .env.example            # 환경 변수 템플릿
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
| **DEVICE** | `cuda` | `cpu` |
| **WHISPER_DEVICE** | `cuda` | `cpu` |
| **DIARIZATION_DEVICE** | `cuda` | `cpu` |
| **SIXDREPNET_DEVICE** | `cuda` | `cpu` |
| **RABBITMQ_HOST** | `localhost` | `rabbitmq` |
| **INPUT_QUEUE** | `analysis.name_non_facing.request` | `analysis.req.task4` |
| **OUTPUT_QUEUE** | `analysis.name_non_facing.result` | `analysis.resp` |
| **LOG_LEVEL** | `DEBUG` | `INFO` |

### 4.3 환경 설정 방법

**로컬 개발 (GPU):**
```bash
# .env.local을 .env로 복사
cp .env.local .env

# HuggingFace 토큰 확인/수정
vi .env
```

**배포 환경 (CPU, EC2):**
```bash
# .env.prod를 .env로 복사
cp .env.prod .env

# HuggingFace 토큰 확인/수정
vi .env
```

### 4.4 의존성 파일 선택

| 환경 | requirements 파일 | Dockerfile | docker-compose |
|------|------------------|------------|----------------|
| 로컬 GPU | `requirements-gpu.txt` | `Dockerfile-gpu` | `docker-compose-gpu.yml` |
| 배포 CPU | `requirements-cpu.txt` | `Dockerfile-cpu` | `docker-compose-cpu.yml` |

### 4.5 .env 파일 예시

```bash
# =============================================================================
# 필수 설정
# =============================================================================
DEVICE=cuda
WHISPER_DEVICE=cuda
DIARIZATION_DEVICE=cuda
SIXDREPNET_DEVICE=cuda

# HuggingFace 토큰 (pyannote 모델용, 필수!)
DIARIZATION_USE_AUTH_TOKEN=hf_xxxxxxxxxxxxxxxx

# =============================================================================
# RabbitMQ 설정
# =============================================================================
RABBITMQ_HOST=localhost        # Docker 내부: rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# =============================================================================
# 큐 설정
# =============================================================================
INPUT_QUEUE=analysis.req.task4
OUTPUT_QUEUE=analysis.resp

# =============================================================================
# 모델 설정
# =============================================================================
YOLO_HEAD_MODEL=models/yolo_p2layer_jh.pt
WHISPER_MODEL_SIZE=large-v3
WHISPER_LANGUAGE=ko

# =============================================================================
# 분석 설정
# =============================================================================
GAZE_ANGLE_THRESHOLD_DEG=20.0      # 시선 반응 판정 각도 임계값
GAZE_STABILIZE_FRAMES=3            # 연속 안정 프레임 수
REACTION_TIMEOUT_SEC=5.0           # 반응 대기 시간
REACTION_MODE=or                   # or / and / gaze_only / voice_only

# =============================================================================
# 로깅
# =============================================================================
LOG_LEVEL=DEBUG
DEBUG=true
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
docker-compose -f docker-compose-gpu.yml up -d name-non-facing-worker

# 로그 확인
docker-compose logs -f name-non-facing-worker
```

### 5.2 RabbitMQ Worker 실행

```bash
python -m app.worker
```

### 5.3 FastAPI 서버 실행 (헬스체크용)

```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
python -m app.main
```

- Health Check: http://localhost:8000/health
- Readiness: http://localhost:8000/ready

### 5.4 테스트 실행

```bash
# 오디오 파이프라인 테스트
python test/test_audio_pipeline.py --video sample_video/name_calling.mp4 --name "은연"

# 비전 파이프라인 테스트
python test/test_vision_pipeline.py

# 전체 파이프라인 테스트
python test/test_pipeline.py
```

---

## 6. 프로젝트 구조

```
name_non_facing/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI 헬스체크 서버
│   ├── worker.py                 # RabbitMQ 워커 (메인 진입점)
│   ├── config.py                 # 환경 설정 (pydantic-settings)
│   ├── models/                   # AI 모델 래퍼
│   │   ├── base.py               # BaseModel (싱글톤, 지연로딩)
│   │   ├── head_detector.py      # YOLO Head 래퍼
│   │   ├── head_pose_6d.py       # 6DRepNet360 래퍼
│   │   ├── speech_recognizer.py  # faster-whisper 래퍼
│   │   ├── speaker_diarizer.py   # pyannote-audio 래퍼
│   │   ├── vad.py                # Silero VAD 래퍼
│   │   └── child_voice_analyzer.py # 음성 반응 통합 분석
│   ├── pipeline/                 # 분석 파이프라인
│   │   ├── orchestrator.py       # FullPipelineOrchestrator
│   │   ├── context.py            # PipelineContext (공유 상태)
│   │   └── stages/
│   │       ├── base_stage.py     # BaseStage 추상 클래스
│   │       ├── input_stage.py    # 오디오 추출 (FFmpeg)
│   │       ├── head_detect_stage.py   # YOLO 머리 검출
│   │       ├── trigger_stage.py  # 호명 탐지 (Whisper)
│   │       ├── child_analysis_stage.py # 시선 분석 (6DRepNet360)
│   │       ├── reaction_detect_stage.py # 음성 반응 탐지
│   │       └── result_stage.py   # 최종 결과 집계
│   ├── core/                     # 핵심 비즈니스 로직
│   │   ├── gaze_analyzer.py      # 시선 반응 분석
│   │   ├── gaze_calculator.py    # Euler → Gaze Vector 변환
│   │   ├── angle_calculator.py   # 벡터 각도 계산
│   │   ├── trial_manager.py      # Trial별 결과 관리
│   │   └── latency_tracker.py    # 반응 지연 추적
│   ├── services/
│   │   └── rabbitmq.py           # RabbitMQ 연결 관리
│   └── utils/
│       ├── audio.py              # FFmpeg 오디오 처리
│       ├── video.py              # 프레임 추출
│       ├── visualize.py          # 디버그 시각화
│       └── logger.py             # 로깅 설정
├── models/                       # 모델 파일 (yolo_p2layer_jh.pt)
├── test/                         # 테스트 코드
├── sample_video/                 # 샘플 비디오
├── output/                       # 디버그 출력
├── docs/                         # 개발 문서
├── docker-compose-gpu.yml
├── docker-compose-cpu.yml
├── requirements-gpu.txt
├── requirements-cpu.txt
└── README.md
```

---

## 7. 파이프라인 흐름

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VIDEO INPUT (S3 URL)                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  InputStage     │ FFmpeg로 오디오 추출 (16kHz mono PCM)                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
         ┌──────────────────────────┴───────────────────────────┐
         ↓ (Vision Branch)                                      ↓ (Audio Branch)
┌─────────────────────────┐                          ┌─────────────────────────┐
│ HeadDetectStage         │                          │ TriggerStage            │
│ YOLO Head (360°)        │                          │ faster-whisper(large-v3)│
│ 부모/아동 머리 검출        │                          │ 호명 구간 탐지 (T_start)  │
└─────────────────────────┘                          └─────────────────────────┘
         ↓                                                      ↓
┌─────────────────────────┐                          ┌─────────────────────────┐
│ ChildAnalysisStage      │                          │ ReactionDetectStage     │
│ 6DRepNet360 (Head Pose) │                          │ Silero VAD + pyannote   │
│ Gaze Vector 계산         │                          │ 음성 반응 탐지            │
│ 시선 반응 분석            │                          │ (Child speaker only)    │
└─────────────────────────┘                          └─────────────────────────┘
         └──────────────────────────┬──────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  ResultStage    │ Vision + Audio 결과 결합 → 반응 판정 → ADOS 점수 산출     │
│                 │ Mode: gaze_only / voice_only / or / and / weighted    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     RabbitMQ OUTPUT (JSON Result)                        │
│  { examId, videoId, status, metrics: {per_trial}, ADOS: {B7, B18} }      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 단계별 요약

| 단계 | 모듈 | 입력 | 출력 |
|:---:|------|------|------|
| 1 | InputStage | 영상 파일 | 프레임 + 오디오 (16kHz) |
| 2 | HeadDetectStage | 프레임 | 부모/아동 머리 위치, Position Vector |
| 3 | TriggerStage | 오디오 | 호명 이벤트 (T_start) |
| 4 | ChildAnalysisStage | 프레임 + 머리 위치 | Gaze Vector, 시선 반응 |
| 5 | ReactionDetectStage | 오디오 + 화자 분리 | 음성 반응 |
| 6 | ResultStage | Vision + Audio 결과 | AnalysisResult, ADOS 점수 |

---

## 8. 모듈별 상세 설명

### 8.1 HeadDetector (YOLO Head)

**역할:** 360° 머리 검출 (뒤통수 포함)

- 모델: `yolo_p2layer_jh.pt` (커스텀 파인튜닝)
- 신뢰도 임계값: 0.15 (낮게 설정하여 민감도 향상)
- 출력: 부모/아동 머리 바운딩 박스 + 중심점

### 8.2 HeadPoseEstimator6D (6DRepNet360)

**역할:** 360° 머리 포즈 추정

- 입력: 머리 ROI 이미지
- 출력: yaw, pitch, roll (각도)
- Gaze Vector 변환: Euler angles → 3D 방향 벡터

**Gaze Vector 계산:**
```python
def euler_to_gaze_vector(yaw_deg, pitch_deg):
    x = -cos(pitch) * sin(yaw)
    y = sin(pitch)
    z = cos(pitch) * cos(yaw)
    return normalize([x, y, z])
```

### 8.3 SpeechRecognizer (faster-whisper)

**역할:** 호명 탐지

- 모델: `large-v3`
- 언어: 한국어 (ko)
- 호명 패턴: `{NAME}아`, `{NAME}야`, `우리 {NAME}` 등
- 출력: 호명 이벤트 (start_time, end_time, text)

### 8.4 SpeakerDiarizer (pyannote-audio)

**역할:** 부모/아동 화자 분리

- 모델: `pyannote/speaker-diarization-3.1`
- 최소 화자 수: 1, 최대: 2
- 출력: 화자별 발화 구간

### 8.5 VoiceActivityDetector (Silero VAD)

**역할:** 음성 구간 검출

- 30ms 청크 단위 처리 (초저지연)
- 임계값: 0.5 (조정 가능)
- 출력: 음성 구간 리스트

### 8.6 GazeAnalyzer

**역할:** 시선 반응 판정

**알고리즘:**
1. 매 프레임 gaze_vector와 position_vector 간 각도 계산
2. 각도 < `GAZE_ANGLE_THRESHOLD_DEG` (20°)가 연속 `GAZE_STABILIZE_FRAMES` (3프레임) 유지 → 반응 감지
3. Latency = T_react - T_start

---

## 9. RabbitMQ 연동

### 9.1 큐 설정

| 큐 | 방향 | 용도 |
|----|------|------|
| `analysis.req.task4` | BE → AI | 분석 요청 수신 |
| `analysis.resp` | AI → BE | 분석 결과 발행 |

### 9.2 입력 메시지 (BE → AI)

```json
{
  "examId": "uuid-1234",
  "videoId": "uuid-5678",
  "videoType": "NAME_NON_FACING",
  "childName": "정현",
  "ageMonths": 36,
  "s3Uri": "https://s3.../video.mp4"
}
```

### 9.3 출력 메시지 (AI → BE)

```json
{
  "examId": "uuid-1234",
  "videoId": "uuid-5678",
  "videoType": "NAME_NON_FACING",
  "analyzedAt": "2026-02-09T10:30:00+09:00",
  "status": "SUCCESS",
  "metrics": {
    "per_trial": [
      {
        "trial_index": 1,
        "success": true,
        "reaction_type": "GAZE",
        "latency_s": 0.45,
        "gaze_latency_s": 0.45,
        "voice_latency_s": null,
        "gaze_duration_s": 2.3,
        "gaze_match": true,
        "voice_detected": false
      },
      {
        "trial_index": 2,
        "success": true,
        "reaction_type": "BOTH",
        "latency_s": 0.62,
        "gaze_latency_s": 0.62,
        "voice_latency_s": 0.85,
        "gaze_duration_s": 1.8,
        "gaze_match": true,
        "voice_detected": true
      }
    ]
  },
  "ADOS": {
    "B7": 0,
    "B18": true
  }
}
```

### 9.4 ADOS 점수 설명

| 항목 | 타입 | 설명 |
|------|------|------|
| B7 | 0-3 | 호명반응 수준 (0=정상 반응, 3=반응 없음) |
| B18 | boolean | 사회적 참조 여부 |

---

## 10. 지표 및 조작적 정의

### 10.1 핵심 지표

| 지표 | 설명 |
|------|------|
| **시선 벡터 (Gaze Vector)** | 머리 방향을 나타내는 3D 단위 벡터 |
| **위치 벡터 (Position Vector)** | 아동 → 부모 방향 2D 벡터 |
| **반응 지연 (Latency)** | 호명 종료 ~ 최초 반응 시작 시간 |
| **시선 유지 시간 (Duration)** | 부모를 향한 시선 지속 시간 |

### 10.2 반응 판정 모드

| 모드 | 설명 |
|------|------|
| `gaze_only` | 시선 반응만 판정 |
| `voice_only` | 음성 반응만 판정 |
| `or` | 시선 OR 음성 (기본값) |
| `and` | 시선 AND 음성 |
| `weighted` | 가중치 조합 |

### 10.3 반응 유형

| 유형 | 조건 |
|------|------|
| `GAZE` | 시선 반응만 감지 |
| `VOICE` | 음성 반응만 감지 |
| `BOTH` | 시선 + 음성 모두 감지 |
| `NONE` | 반응 없음 |

---

## 11. 설정 옵션

### 11.1 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| DEVICE | 메인 연산 장치 | cuda |
| WHISPER_DEVICE | Whisper 연산 장치 | cuda |
| DIARIZATION_DEVICE | pyannote 연산 장치 | cuda |
| SIXDREPNET_DEVICE | 6DRepNet 연산 장치 | cuda |
| DIARIZATION_USE_AUTH_TOKEN | HuggingFace 토큰 | (필수) |
| YOLO_HEAD_MODEL | YOLO 모델 경로 | models/yolo_p2layer_jh.pt |
| WHISPER_MODEL_SIZE | Whisper 모델 크기 | large-v3 |
| WHISPER_LANGUAGE | 음성 인식 언어 | ko |

### 11.2 분석 설정

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| GAZE_ANGLE_THRESHOLD_DEG | 시선 반응 각도 임계값 | 20.0 |
| GAZE_STABILIZE_FRAMES | 안정화 프레임 수 | 3 |
| REACTION_TIMEOUT_SEC | 반응 대기 시간 | 5.0 |
| REACTION_MODE | 반응 판정 모드 | or |
| VAD_THRESHOLD | VAD 임계값 | 0.5 |

---

## 12. 트러블슈팅

### 12.1 pyannote 모델 다운로드 실패

```bash
# HuggingFace 로그인 확인
huggingface-cli whoami

# 토큰 재설정
huggingface-cli login

# 모델 라이선스 동의 확인
# https://huggingface.co/pyannote/speaker-diarization-3.1 접속 후 동의
```

### 12.2 YOLO 모델 파일 없음

```bash
# 모델 파일 확인
ls -la models/yolo_p2layer_jh.pt

# 없으면 Google Drive에서 다운로드
# https://drive.google.com/file/d/1PeAzKYBAf5r-btK24KU180nWkMmRHTWN/view
```

### 12.3 CUDA 관련

```bash
# CUDA 버전 확인
nvidia-smi

# PyTorch CUDA 확인
python -c "import torch; print(torch.cuda.is_available())"
```

### 12.4 FFmpeg 없음

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg
```

### 12.5 에러 코드별 대응

| 에러 | 원인 | 해결 방법 |
|------|------|----------|
| `401 Unauthorized` | HuggingFace 토큰 문제 | 토큰 재발급 및 .env 설정 |
| `YOLO model not found` | 모델 파일 누락 | Google Drive에서 다운로드 |
| `No audio track` | 영상에 오디오 없음 | 오디오 포함 영상 사용 |
| `No faces detected` | 얼굴 미검출 | 촬영 환경 개선 |

---

*Last Updated: 2026-02-09*
