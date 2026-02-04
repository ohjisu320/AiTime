# 기능 명세서: 아기 감정 추출 (Child Emotion Extraction)

## 1. 개요
"호명 반응(Face-to-Face Name Response)" 과제 분석 시, 아기의 **감정 상태(8가지)**를 분석합니다.

---

## 2. 기술 스택
| 항목 | 선택 |
|:--|:--|
| 라이브러리 | `EmotiEffLib` (ONNX Backend) / `hsemotion` (Fallback) |
| 환경 | AWS EC2 (CPU) |
| 모델 | `enet_b0_8_best_vgaf` |
| 감정 클래스 | Anger, Contempt, Disgust, Fear, Happiness, Neutral, Sadness, Surprise |

---

## 3. 설계 결정

| 항목 | 결정 |
|:--|:--|
| Confidence Threshold | 없음 (최대값 사용) |
| Debug Overlay | 사용 (`/debug/mjpeg`에 표시) |
| Graceful Degradation | 모델 로드 실패 시 비활성화 |

---

## 4. 수정 대상 파일 및 내용

### 4.1 의존성
**`requirements.txt`**
- `EmotiEffLib>=0.1.0`
- `onnxruntime>=1.15.0`

### 4.2 설정
**`app/rtn/config.py`**
```python
@dataclass(frozen=True)
class EmotionConfig:
    enable: bool = True
    skip_frames: int = 5
    min_face_size: int = 64
    model_name: str = "enet_b0_8_best_vgaf"
    p95_latency_ms_max: int = 50
```

### 4.3 핵심 모듈
**`app/rtn/emotion/emotion_recognizer.py`** [신규]
```python
class EmotionRecognizer:
    def __init__(self, cfg: EmotionConfig):
        # EmotiEffLib 없으면 hsemotion으로 Fallback 시도
        ...
    def predict(self, face_bgr: FrameBGR) -> dict[str, float] | None: ...
```

### 4.4 결과 스키마
**`app/rtn/pipeline/results.py`**
```python
@dataclass
class CallResult:
    # 기존 필드 유지
    dominant_emotion: str | None = None
    emotion_distribution: dict[str, float] | None = None
    meta: dict[str, object] | None = None
```

### 4.5 파이프라인 통합
**`app/rtn/pipeline/window_analyzer.py`**
- 루프 내 `child_crop` → `EmotionRecognizer.predict()` 호출
- 결과 `emotion_samples` 리스트에 누적
- 종료 시 평균 분포 산출 → `CallResult`에 저장
- Debug Overlay: `cv2.putText(dbg, "Happy 85%", ...)` 추가

**`app/rtn/pipeline/video_analyzer.py`**
- `per_call` 딕셔너리에 `dominant_emotion`, `emotion_distribution` 필드 추가

### 4.6 Factory/Engine 통합
**`app/rtn/factory.py`**
- `EmotionConfig` 생성 및 `WindowAnalyzer` 전달

**`app/rtn/service/engine.py`**
- `build_engine` 파라미터에 `emotion_enable: bool = True` 추가 (선택적)

---

## 5. 검증 계획
- **Unit Test**: 
    - `tests/unit/test_emotion_logic.py`
    - `tests/unit/test_video_analyzer_emotion_output.py`
- **Manual Test**: `/debug/mjpeg` 스트림에서 감정 오버레이 확인

---

## 6. 참고: 프로젝트 전체 구조
```
app/
├── main.py                     # FastAPI 앱 (수정 없음)
├── worker.py                   # RabbitMQ 워커 (수정 없음, 결과 자동 포함)
└── rtn/
    ├── config.py               # [수정] EmotionConfig 추가
    ├── factory.py              # [수정] EmotionConfig 생성
    ├── emotion/                # [신규]
    │   └── emotion_recognizer.py
    ├── pipeline/
    │   ├── results.py          # [수정] CallResult 필드 추가
    │   ├── window_analyzer.py  # [수정] 감정 분석 로직 + 오버레이
    │   └── video_analyzer.py   # [수정] per_call 딕셔너리 확장
    ├── debug/
    │   ├── broker.py           # 수정 없음 (JPEG publish)
    │   └── renderer.py         # 수정 없음 (cv2 window)
    └── service/
        └── engine.py           # [수정] emotion_enable 파라미터
```
