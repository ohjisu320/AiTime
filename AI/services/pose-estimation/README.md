# Pose Estimation Service

# 도커 실행 법
```bash
# 전체 서비스 실행
docker-compose up -d

# Worker만 실행 (RabbitMQ 외부 사용시)
docker-compose up -d pose-worker

# 로그 확인
docker-compose logs -f pose-worker
```

# 목표 응답 구조
```json
{
  "exam_id": "uuid",
  "video_type": "POSE_IMITATION",
  "analyzed_at": "YYYY-MM-DDTHH:mm:ss+09:00",
  "status": "completed",
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
        "action_type": "waving",
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


> **ViTPose 기반 동작 모방 분석 파이프라인**  
> 부모의 동작을 아이가 얼마나 잘 따라하는지 정량적으로 분석합니다.

---

## 📑 목차

1. [개요](#1-개요)
2. [설치 및 환경 설정](#2-설치-및-환경-설정)
3. [실행 방법](#3-실행-방법)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [파이프라인 흐름](#5-파이프라인-흐름)
6. [모듈별 상세 설명](#6-모듈별-상세-설명)
7. [API 명세](#7-api-명세)
8. [설정 옵션](#8-설정-옵션)
9. [지원 동작](#9-지원-동작)
10. [트러블슈팅](#10-트러블슈팅)

---

## 1. 개요

### 1.1 서비스 목적
- **영상 입력** → **부모/아이 자세 추출** → **동작 유사도 분석** → **결과 반환**
- 아이의 동작 모방 능력을 정량적 수치로 제공
- 발달 검사 도구로 활용 가능

### 1.2 핵심 기능
- ✅ **부모-아이 역할 자동 식별** (몸통 크기 기반)
- ✅ **6가지 동작 유형 지원** (만세, 박수, 점프, 발차기, 던지기, 뒤로걷기)
- ✅ **반응 지연 시간 측정** (부모 동작 시작 → 아이 동작 시작)
- ✅ **프레임별 유사도 계산** (DTW 정렬 + 유클리드 거리 기반)
- ✅ **스켈레톤 시각화** (부모=파란색, 아이=주황색)

### 1.3 기술 스택
| 분류 | 기술 |
|:---|:---|
| Pose Estimation | ViTPose (HuggingFace transformers) |
| Person Detection | RT-DETR |
| DTW 정렬 | dtw-python (C-accelerated) |
| Backend | FastAPI, RabbitMQ |
| 영상 처리 | OpenCV, Pillow |
| Deep Learning | PyTorch 2.5 |

---

## 2. 설치 및 환경 설정

### 2.1 Conda 환경 생성
```bash
conda create -n pose-worker python=3.11 -y
conda activate pose-worker
```

### 2.2 의존성 설치
```bash
pip install -r requirements.txt
```

### 2.3 GPU 지원 (권장)
```bash
# CUDA 12.x 기준
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

### 2.4 환경 변수 설정 (선택)
```bash
# .env 파일 생성
echo "DEVICE=cuda" > .env
echo "LOG_LEVEL=INFO" >> .env
echo "DEBUG_MODE=false" >> .env
```

---

## 3. 실행 방법

### 3.1 CLI 분석 (가장 간단)
```bash
# 기본 사용법
python -m app.pipeline.analyzer <영상경로> <동작유형> --age <월령>

# 예시: 만세 동작 분석
python -m app.pipeline.analyzer video.mp4 hurray --age 18

# 시각화 포함 (스켈레톤 오버레이 이미지/동영상 생성)
python -m app.pipeline.analyzer video.mp4 hurray --age 18 --visualize

# 상세 로그 출력
python -m app.pipeline.analyzer video.mp4 hurray --age 18 --verbose
```

### 3.2 CLI 옵션 전체
| 옵션 | 설명 | 기본값 |
|:---|:---|:---|
| `--age`, `-a` | 아동 월령 (12-24) | 18 |
| `--visualize`, `-v` | 시각화 활성화 | False |
| `--output`, `-o` | 시각화 출력 폴더 | `analysis_output` |
| `--no-video` | 스켈레톤 동영상 생성 안함 | False |
| `--no-parent-ref` | 부모 참조 비활성화 | False |
| `--no-role-identify` | 역할 식별 비활성화 | False |
| `--no-smooth` | 스무딩 비활성화 | False |
| `--smooth-method` | 스무딩 방법 | `one_euro` |
| `--verbose` | 상세 로그 | False |

### 3.3 FastAPI 서버 실행
```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
python -m app.main
```
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3.4 RabbitMQ Worker 실행
```bash
python -m app.worker
```

### 3.5 Docker 실행
```bash
# 이미지 빌드
docker build -t pose-worker .

# GPU 지원 실행
docker run --gpus all -p 8000:8000 pose-worker
```

---

## 4. 프로젝트 구조

```
pose-estimation/
├── app/
│   ├── __init__.py
│   ├── config.py              # 환경 설정 (pydantic-settings)
│   ├── main.py                # FastAPI 엔드포인트
│   ├── worker.py              # RabbitMQ 워커
│   ├── models/
│   │   └── vitpose.py         # ViTPose 모델 래퍼
│   ├── pipeline/
│   │   ├── analyzer.py        # ⭐ 통합 파이프라인 (진입점)
│   │   ├── video_processor.py # 영상 → 프레임 추출
│   │   ├── pose_extractor.py  # 프레임 → 2D 포즈
│   │   ├── normalizer.py      # 정규화 + 역할 식별 + 스무딩
│   │   ├── dtw.py             # 시간 정렬 (DTW)
│   │   ├── similarity.py      # 유사도 계산
│   │   └── exceptions.py      # 커스텀 예외
│   ├── utils/
│   │   ├── validators.py      # 입력 검증
│   │   └── visualize.py       # 스켈레톤 시각화
│   └── references/            # (미사용) JSON 기준 동작 데이터
├── tests/                     # 테스트 코드
├── docs_0125/                 # 개발 문서
├── requirements.txt           # Python 의존성
├── Dockerfile                 # 컨테이너 빌드
└── pyproject.toml             # 프로젝트 메타데이터
```

---

## 5. 파이프라인 흐름

### 5.1 전체 흐름도
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         analyze() 메인 파이프라인                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐    ┌──────────────┐    ┌────────────────┐               │
│   │  VIDEO   │───▶│ VideoProcessor│───▶│ PoseExtractor  │               │
│   │  INPUT   │    │ (프레임 추출) │    │ (ViTPose 추론) │               │
│   └──────────┘    └──────────────┘    └───────┬────────┘               │
│                                               │                         │
│                                               ▼                         │
│                                     ┌────────────────┐                  │
│                                     │  PoseNormalizer │                  │
│                                     │ (정규화+역할식별)│                  │
│                                     └───────┬────────┘                  │
│                                             │                           │
│                          ┌──────────────────┴──────────────────┐        │
│                          ▼                                     ▼        │
│                  ┌──────────────┐                     ┌──────────────┐  │
│                  │ Parent Seq   │                     │ Child Seq    │  │
│                  │ (부모 시퀀스) │                     │ (아이 시퀀스)│  │
│                  └──────┬───────┘                     └──────┬───────┘  │
│                         │                                    │          │
│                         ▼                                    ▼          │
│                  ┌─────────────────────────────────────────────┐        │
│                  │         _calculate_reaction_delay           │        │
│                  │  (동작별 특화 알고리즘으로 시작 프레임 감지)   │        │
│                  └────────────────────┬────────────────────────┘        │
│                                       │                                 │
│                                       ▼                                 │
│                              ┌───────────────┐                          │
│                              │   DTWAligner  │                          │
│                              │ (시간축 정렬)  │                          │
│                              └───────┬───────┘                          │
│                                      │                                  │
│                                      ▼                                  │
│                          ┌────────────────────┐                         │
│                          │ SimilarityCalculator│                         │
│                          │ (유클리드 거리 역수)│                         │
│                          └─────────┬──────────┘                         │
│                                    │                                    │
│                                    ▼                                    │
│                           ┌────────────────┐                            │
│                           │ AnalysisResult │                            │
│                           └────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 단계별 설명

| 단계 | 모듈 | 입력 | 출력 | 설명 |
|:---:|:---|:---|:---|:---|
| 1 | `VideoProcessor` | 영상 파일 | 프레임 이미지 | FPS 맞춰 프레임 추출 (10fps) |
| 2 | `PoseExtractor` | 프레임 | 17개 관절 좌표 | ViTPose로 2D 포즈 추정 |
| 3 | `PoseNormalizer` | 관절 좌표 | 정규화 시퀀스 | 몸통 기준 정규화, 역할 식별 |
| 4 | 반응 지연 계산 | 부모/아이 시퀀스 | delay_sec | 동작 시작 시점 차이 계산 |
| 5 | `DTWAligner` | query, ref | aligned | 시간축 정렬 (속도 보정) |
| 6 | `SimilarityCalculator` | aligned pair | score | 프레임별 유사도 계산 |
| 7 | 결과 집계 | 모든 메트릭 | `AnalysisResult` | pass/fail, 점수, 시간 정보 |

---

## 6. 모듈별 상세 설명

### 6.1 VideoProcessor (`video_processor.py`)
**역할**: 영상 파일을 프레임 이미지로 분해

```python
# 주요 메서드
extract_frames(video_path)  # Generator 방식 (메모리 효율)
extract_frames_to_folder(video_path, output_folder)  # 폴더 저장 방식
get_video_info(video_path)  # 영상 메타데이터
```

**설정 가능 항목**:
- `TARGET_FPS`: 추출 프레임 레이트 (기본: 10)
- `MAX_VIDEO_FRAMES`: 최대 프레임 수 (기본: 300)
- `MAX_VIDEO_DURATION_SEC`: 최대 영상 길이 (기본: 30초)

---

### 6.2 PoseExtractor (`pose_extractor.py`)
**역할**: 프레임에서 2D 관절 좌표 추출

```python
# 주요 메서드
extract_from_frames(frames)  # Generator 입력
extract_from_folder(folder)  # 폴더 입력

# 출력 형태
FrameData(frame_idx, persons=[PersonData(keypoints, bbox)])
```

**사용 모델**:
- Person Detection: `PekingU/rtdetr_r50vd_coco_o365`
- Pose Estimation: `usyd-community/vitpose-base-simple`

**키포인트 구성 (COCO 17 형식)**:
```
0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear,
5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow,
9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip,
13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle
```

---

### 6.3 PoseNormalizer (`normalizer.py`)
**역할**: 정규화, 역할 식별, 스무딩

```python
# 주요 메서드
normalize_and_smooth(frames_data, identify_roles=True, smooth=True)

# 출력
{
    "parent_sequence": np.array(T, 17, 3),  # 부모 시퀀스
    "child_sequence": np.array(T, 17, 3),   # 아이 시퀀스
    "frame_persons": [FramePersons(...)]     # 프레임별 역할 정보
}
```

**정규화 방식**:
- 몸통 중심(어깨-골반) 기준으로 좌표 변환
- 몸통 길이 기준으로 스케일 정규화
- 카메라 거리에 불변한 상대 좌표

**역할 식별 로직**:
- 몸통 길이가 더 큰 사람 → 부모
- 몸통 길이가 더 작은 사람 → 아이

**스무딩 방법**:
- `one_euro`: 1€ 필터 (기본, 권장)
- `ema`: 지수 이동 평균
- `moving_average`: 단순 이동 평균

---

### 6.4 DTWAligner (`dtw.py`)
**역할**: Dynamic Time Warping으로 시간축 정렬

```python
# 주요 메서드
align_sequences(query, reference)  # 시퀀스 정렬
compute_dtw(query, reference)      # DTW 거리 계산

# 출력
(aligned_query, aligned_reference)  # 동일 길이 시퀀스
```

**사용 라이브러리**: `dtw-python` (C-accelerated)

**Sakoe-Chiba 밴드**: 정렬 경로 제약으로 속도/정확도 균형

---

### 6.5 SimilarityCalculator (`similarity.py`)
**역할**: 정렬된 시퀀스 간 유사도 계산

```python
# 주요 메서드
compute_similarity(query, reference, aligned=True)

# 출력
SimilarityResult(
    overall=0.85,           # 전체 유사도
    upper_body=0.90,        # 상체 점수
    lower_body=0.80,        # 하체 점수
    head=0.85,              # 머리 점수
    frame_similarities=[...] # 프레임별 점수
)
```

**유사도 공식**:
```
similarity = 1 / (1 + euclidean_distance)
```
- 유클리드 거리가 0이면 유사도 1
- 거리가 클수록 유사도 0에 수렴

**가중치 적용**:
- 상체: 1.5배 (상체 동작 중요)
- 하체: 1.0배
- 머리: 0.5배

---

### 6.6 반응 지연 감지 (analyzer.py 내부)
**역할**: 동작별 특화 알고리즘으로 시작 시점 감지

| 동작 | 감지 방법 | 조건 |
|:---|:---|:---|
| `hurray` | 손목 위치 | 양쪽 손목 > 어깨 + margin |
| `clapping` | 손목 간 거리 | 거리 < threshold |
| `jumping` | 엉덩이 y좌표 | 초기 대비 상승 |
| `kicking` | 발목 높이 차이 | 좌우 발목 높이 차 > threshold |
| `throwing` | 손목 위치 | 한쪽 손목 > 어깨 |
| `walking_back` | 골반 x좌표 | 초기 대비 이동 |

---

## 7. API 명세

### 7.1 분석 요청
```http
POST /analyze
Content-Type: multipart/form-data

video: <file>          # 영상 파일
action_type: hurray    # 동작 유형
age_months: 18         # 아동 월령
```

### 7.2 분석 결과
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
        "child_torso_length": 89.4,
        "reaction_delay_detail": {
            "parent_start_frame": 5,
            "parent_start_sec": 0.5,
            "child_start_frame": 12,
            "child_start_sec": 1.2,
            "delay_frames": 7,
            "detection_method": "wrist_position"
        }
    },
    "details": {
        "upper_body_score": 0.88,
        "lower_body_score": 0.76,
        "head_score": 0.82,
        "total_frames_analyzed": 45,
        "valid_frame_ratio": 0.95,
        "video_duration_sec": 4.5,
        "video_fps": 10.0
    }
}
```

### 7.3 에러 응답
```json
{
    "error_code": "PARENT_NOT_DETECTED",
    "message": "부모 시퀀스를 감지하지 못했습니다. 부모와 아이가 함께 있는 영상이 필요합니다.",
    "details": {
        "video_path": "video.mp4"
    }
}
```

---

## 8. 설정 옵션

### 8.1 환경 변수 (`.env` 또는 시스템)
| 변수명 | 설명 | 기본값 |
|:---|:---|:---|
| `DEVICE` | 연산 장치 (cuda/cpu/mps) | `cuda` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |
| `DEBUG_MODE` | 디버그 모드 | `false` |
| `TARGET_FPS` | 프레임 추출 FPS | `10.0` |
| `MAX_VIDEO_DURATION_SEC` | 최대 영상 길이 | `30.0` |

### 8.2 동작별 판정 임계값
| 동작 | 임계값 | 설정 변수 |
|:---|:---:|:---|
| clapping | 0.70 | `THRESHOLD_CLAPPING` |
| hurray | 0.65 | `THRESHOLD_HURRAY` |
| walking_back | 0.60 | `THRESHOLD_WALKING_BACK` |
| jumping | 0.65 | `THRESHOLD_JUMPING` |
| kicking | 0.60 | `THRESHOLD_KICKING` |
| throwing | 0.65 | `THRESHOLD_THROWING` |

---

## 9. 지원 동작

### 9.1 동작 목록
| 동작 | 영문 | 설명 | 난이도 |
|:---|:---|:---|:---:|
| 만세 | hurray | 양팔을 머리 위로 올림 | ⭐ |
| 박수 | clapping | 양손을 마주침 | ⭐⭐ |
| 점프 | jumping | 제자리에서 뛰어오름 | ⭐⭐ |
| 발차기 | kicking | 한 발로 공 차는 동작 | ⭐⭐ |
| 던지기 | throwing | 공을 던지는 동작 | ⭐⭐ |
| 뒤로걷기 | walking_back | 뒤로 걸어감 | ⭐⭐⭐ |

### 9.2 촬영 가이드
- ✅ **부모와 아이가 함께** 촬영되어야 함
- ✅ **전신이 보이도록** 촬영 (발끝~머리)
- ✅ **정면 또는 측면** 촬영 권장
- ✅ **5-10초** 분량이면 충분
- ❌ 너무 가까이에서 촬영하면 관절 감지 실패
- ❌ 부모/아이 중 한 명만 있으면 에러

---

## 10. 트러블슈팅

### 10.1 CUDA 관련
```bash
# CUDA 버전 확인
nvidia-smi

# PyTorch CUDA 확인
python -c "import torch; print(torch.cuda.is_available())"
```

### 10.2 모델 다운로드 실패
```bash
# HuggingFace 캐시 초기화
rm -rf ~/.cache/huggingface/hub

# 수동 다운로드
python -c "from transformers import AutoModel; AutoModel.from_pretrained('usyd-community/vitpose-base-simple')"
```

### 10.3 에러 코드별 대응
| 에러 코드 | 원인 | 해결 방법 |
|:---|:---|:---|
| `PARENT_NOT_DETECTED` | 부모 미감지 | 부모와 아이 함께 촬영 |
| `CHILD_NOT_DETECTED` | 아이 미감지 | 부모와 아이 함께 촬영 |
| `VIDEO_PROCESSING_ERROR` | 영상 파일 문제 | 지원 포맷 확인 (mp4, webm, avi, mov) |
| `POSE_EXTRACTION_ERROR` | 관절 추출 실패 | 전신이 보이도록 재촬영 |

### 10.4 성능 최적화
- **GPU 사용**: CPU 대비 10배 이상 빠름
- **FPS 조절**: 빠른 동작이 아니면 5fps로도 충분
- **영상 길이**: 30초 이하 권장

