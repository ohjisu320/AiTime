# 기능 명세서: 아이 표정 분석 (ADOS B6 판정)

## 1. 개요
"동작 모방(Pose Imitation)" 과제 분석 시, 아이의 **표정**을 분석하여 **ADOS B6 (즐거움 공유)** 점수를 산출합니다.

**핵심 로직**: Happiness 비율 ≥ `joy_threshold` (기본 10%) → **ADOS B6 = True**

---

## 2. 기술 스택
| 항목 | 선택 |
|:--|:--|
| 표정 분류 | `EmotiEffLib` (ONNX Backend) / `hsemotion` (Fallback) |
| 얼굴 탐지 | `RetinaFace` (ONNX) |
| 환경 | AWS EC2 (GPU/CPU) |
| 모델 | `enet_b0_8_best_vgaf` |
| 감정 클래스 | Anger, Contempt, Disgust, Fear, Happiness, Neutral, Sadness, Surprise |

---

## 3. 설계 결정

| 항목 | 결정 |
|:--|:--|
| 프레임 샘플링 | 매 5프레임 (`skip_frames=5`) |
| 아이 식별 | Pose 기반 역할 매칭 (기존 분석 결과 활용) |
| ADOS B6 판정 | Happiness 비율 ≥ `joy_threshold` (config에서 설정, 기본 0.1) |
| 최소 얼굴 크기 | 64px |
| Graceful Degradation | 모델 로드 실패 시 Fallback 로직 사용 |

---

## 4. 수정 대상 파일 및 내용

### 4.1 의존성
**`requirements.txt`**
```
# Emotion Recognition
EmotiEffLib>=0.1.0
onnxruntime>=1.15.0

# Face Detection
retinaface-pytorch>=0.0.8
```

### 4.2 설정
**`app/config.py`**
```python
# =========================================================================
# 표정 분석 설정
# =========================================================================
@dataclass(frozen=True)
class EmotionConfig:
    enable: bool = True
    skip_frames: int = 5
    min_face_size: int = 64
    model_name: str = "enet_b0_8_best_vgaf"
    joy_threshold: float = 0.1  # Happiness 비율 >= 10%이면 ADOS B6 = True
    face_confidence_threshold: float = 0.9
```

### 4.3 핵심 모듈

**`app/pipeline/emotion/__init__.py`** [신규]
```python
from .face_detector import FaceDetector
from .child_selector import ChildFaceSelector
from .emotion_recognizer import EmotionRecognizer
from .expression_analyzer import ExpressionAnalyzer
```

**`app/pipeline/emotion/face_detector.py`** [신규]
```python
@dataclass
class FaceDetection:
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    landmarks: np.ndarray | None  # 5 keypoints

class FaceDetector:
    def __init__(self, min_face_size: int = 64): ...
    def detect(self, frame_bgr: np.ndarray) -> list[FaceDetection]: ...
```

**`app/pipeline/emotion/child_selector.py`** [신규]
```python
class ChildFaceSelector:
    def select(
        self,
        faces: list[FaceDetection],
        child_head_pos: tuple[float, float] | None  # Pose 기반 머리 위치
    ) -> FaceDetection | None: ...
```

**`app/pipeline/emotion/emotion_recognizer.py`** [신규]
```python
class EmotionRecognizer:
    def __init__(self, model_name: str = "enet_b0_8_best_vgaf"):
        # EmotiEffLib 없으면 hsemotion으로 Fallback 시도
        ...
    def predict(self, face_bgr: np.ndarray) -> dict[str, float] | None: ...
```

**`app/pipeline/emotion/expression_analyzer.py`** [신규]
```python
@dataclass
class ExpressionResult:
    total_frames_analyzed: int
    valid_detections: int
    expression_counts: dict[str, int]
    expression_ratios: dict[str, float]
    joy_count: int
    joy_ratio: float
    joy_detected: bool
    dominant_emotion: str
    processing_time_sec: float

class ExpressionAnalyzer:
    def __init__(self, cfg: EmotionConfig): ...
    def analyze(
        self,
        frames: list[np.ndarray],
        child_positions: list[tuple[float, float] | None]
    ) -> ExpressionResult: ...
```

### 4.4 결과 스키마
**`app/pipeline/analyzer.py`**
```python
@dataclass
class MultiTrialAnalysisResult:
    assessment_type: str
    age_months: int
    processing_time_sec: float
    metrics: dict[str, list[dict[str, Any]]]
    ados: dict[str, Any]  # {"B6": bool, "A8": int, "B18": bool}
    role_info: Optional[dict[str, Any]] = None
    details: dict[str, Any] = field(default_factory=dict)
```

**ADOS B6 판정 로직**:
```python
# Happiness 비율이 joy_threshold 이상이면 B6 = True
joy_ratio = expression_result.joy_ratio  # 0.0 ~ 1.0
ados_scores["B6"] = joy_ratio >= EmotionConfig.joy_threshold
```

### 4.5 파이프라인 통합
**`app/pipeline/analyzer.py`**
```python
class MotionAnalyzer:
    def __init__(self):
        # 기존 초기화
        self.video_processor = VideoProcessor()
        self.pose_extractor = PoseExtractor()
        # ...
        
        # 표정 분석 초기화
        self.expression_analyzer = ExpressionAnalyzer(EmotionConfig())
    
    def analyze_multi_trial(self, video_path: str, ...) -> MultiTrialAnalysisResult:
        # 기존 분석 로직
        # ...
        
        # 표정 분석 (skip_frames 간격으로 샘플링)
        expression_result = self.expression_analyzer.analyze(
            frames=sampled_frames,
            child_positions=child_head_positions
        )
        
        return MultiTrialAnalysisResult(
            # 기존 필드
            ados={
                "B6": expression_result.joy_ratio >= config.joy_threshold,  # 즐거움 감지
                "A8": a8_score,  # 주의/반응
                "B18": b18_score  # 사회적 모방
            },
            details={
                "expression_analysis": {
                    "method": "expression_analyzer",
                    "joy_ratio": expression_result.joy_ratio,
                    "joy_count": expression_result.joy_count,
                    "frames_analyzed": expression_result.total_frames_analyzed
                }
            }
        )
```

---

## 5. API 응답 형식

```json
{
  "assessment_type": "pose_imitation",
  "age_months": 15,
  "processing_time_sec": 8.42,
  "metrics": { "per_trial": [...] },
  "ados": { 
    "B6": true,   // Happiness 비율 >= joy_threshold (10%)
    "A8": 1, 
    "B18": true 
  },
  "details": {
    "expression_analysis": {
      "method": "expression_analyzer",
      "joy_ratio": 0.38,
      "joy_count": 23,
      "frames_analyzed": 60
    }
  }
}
```

---

## 6. 검증 계획
- **Unit Test**: 
    - `tests/unit/test_face_detector.py`
    - `tests/unit/test_emotion_recognizer.py`
    - `tests/unit/test_expression_analyzer.py`
- **Integration Test**: 
    - `tests/integration/test_analyzer_with_emotion.py`

---

## 7. 프로젝트 구조
```
app/
├── main.py                         # FastAPI 앱 (수정 없음)
├── worker.py                       # RabbitMQ 워커 (결과 자동 포함)
├── config.py                       # [수정] EmotionConfig 추가
├── models/
│   └── vitpose.py                  # 수정 없음
├── pipeline/
│   ├── analyzer.py                 # [수정] 표정 분석 통합
│   ├── video_processor.py          # 수정 없음
│   ├── pose_extractor.py           # 수정 없음
│   ├── normalizer.py               # 수정 없음
│   ├── dtw.py                      # 수정 없음
│   ├── similarity.py               # 수정 없음
│   └── emotion/                    # [신규]
│       ├── __init__.py
│       ├── face_detector.py
│       ├── child_selector.py
│       ├── emotion_recognizer.py
│       └── expression_analyzer.py
└── utils/
    └── ...                         # 수정 없음
```
