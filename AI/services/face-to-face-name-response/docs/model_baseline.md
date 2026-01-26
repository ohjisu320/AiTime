
# Model Baseline: RTN Eye-Contact (VAD → Face/Track → Role → Iris Gaze → ROI Raycast)

이 문서는 “호명 반응(이름 부르기) 이후 아이가 부모를 바라봤는지”를 **학습 없이(휴리스틱/기성 모델 조합)** 추정하는 베이스라인의 설계/개발 히스토리/한계/후속 계획을 정리합니다.

---

## 1. Task Definition (과제 정의)

### Input
- 단일 동영상 파일 (부모 + 아이가 함께 등장)

### Output (per call)
호명 시도별로 아래를 계산합니다.

- `success`: eye-contact 성공 여부
- `latency_s`: `call_end` 이후 첫 eye-contact까지의 시간(초)
- `gaze_duration_s`: eye-contact가 유지된 총 시간(초)

### Summary
- `success_count / total_call_count`
- `avg_latency_s`
- `total_gaze_duration_s`

---

## 2. High-level Pipeline

분석은 “전체 동영상에서 호명 구간을 잡고, 각 호명 종료 시점 이후 반응(window)을 본다”는 구조입니다.

1) **VAD(Silero)** 로 발화(speech) 구간을 검출하여 호명 후보 구간 리스트를 생성  
2) 각 구간에 대해 `call_end ~ call_end + window_s` 프레임을 분석  
3) 프레임마다:
   - 얼굴 검출(MediaPipe FaceDetection) → 추적(SORT)
   - role assignment(부모/아이)
   - 아이 FaceMesh/Iris로 2D gaze ray 추정
   - 부모 eye ROI 마스크 생성(mesh 가능 시 mesh 기반, 아니면 bbox fallback)
   - gaze ray가 ROI 마스크를 관통하면 contact=True
4) `min_contact_frames` 연속 contact이면 success로 판정 + latency 기록

---

## 3. Modules & Code Pointers

### 3.1 VAD
- `app/rtn/audio/ffmpeg.py` : 영상에서 wav 추출 (ffmpeg 필요)
- `app/rtn/audio/vad_silero.py` : Silero VAD(torch.hub)
- `app/rtn/audio/segments.py` : segment merge 등 유틸
- 파라미터:  
  - `sr=16000`, `min_speech_ms=250`, `min_silence_ms=250`, `merge_gap_s=0.3`

**Why VAD first?**
- 과제는 “호명 이후 반응”이므로, 호명 후보 시점을 먼저 잡아야 지표가 의미를 가짐.
- 전체 프레임을 보면 무관한 시선이 성공으로 될 수 있고 비용도 증가.

### 3.2 Face Detection & Tracking
- Detect: `app/rtn/vision/mp_face_detector.py`
- Tracking: `app/rtn/tracking/sort_tracker.py` (SORT; scipy 있으면 Hungarian, 없으면 greedy fallback)

**Why tracking?**
- 프레임별 검출만으로는 부모/아이 bbox가 교차 시 swap되는 문제가 잦음.
- eye-contact는 연속 프레임 조건이 중요 → ID continuity 확보가 필수.

### 3.3 Role Assignment (Parent vs Child)
- `app/rtn/pipeline/roles.py`
- Warmup 동안 track별 bbox area 평균을 누적 후 **큰 얼굴=parent**, **작은 얼굴=child**

**Trade-off**
- 단순/빠름
- 거리 역전(아이가 카메라에 더 가까움) 등에서 실패 가능 → 디버그 스트림으로 즉시 확인 가능하게 설계

### 3.4 Child Gaze Estimation (FaceMesh + Iris ratio, 2D)
- `app/rtn/vision/mp_facemesh.py`
- `app/rtn/gaze/iris_ratio.py`
- 핵심 아이디어:
  - iris center가 eye contour 내부에서 어디에 위치하는지로 좌/우/상/하 편향을 추정(dx, dy)
  - smoothing(alpha), jump clamp(max_jump), deadzone 적용
  - 화면 좌표에서 gaze ray end point를 계산(`gaze_scale`)

**Why 2D baseline?**
- 학습 기반 gaze는 데이터/라벨/도메인적응 비용이 큼.
- 초기 모델에서는 gaze 계산으로 가능하다고 판단
- 추후 3D/학습 기반으로 교체 가능한 모듈 구조로 설계.

### 3.5 Parent Eye ROI + Contact
- ROI: `app/rtn/roi/parent_eye_roi.py`
  - parent mesh 가능 → eye contour 기반 mask + dilate
  - mesh 불가 → bbox 상단 영역 ellipse 근사 fallback
- Contact: `app/rtn/roi/contact.py`
  - gaze ray를 `raycast_samples`로 샘플링하여 mask hit이면 contact=True

**Success Rule**
- contact가 True인 프레임이 `min_contact_frames` 연속이면 `first_contact_time` 기록
- `latency_s = first_contact_time - call_end`
- `gaze_duration_s`는 contact True인 프레임마다 `dt`를 누적(연속 조건 전이라도 누적됨)

---

## 4. Window Analysis Details

- 분석 윈도우: `start_t = call_end`, `end_t = call_end + window_s`
- FPS:
  - `cv2.CAP_PROP_FPS` 기반, 없으면 30fps fallback
  - `AnalysisConfig.fps_override`로 강제 가능

- 상태 머신(요약)
  - role 미할당 → debug publish는 계속(스트림이 멈춘 것처럼 보이지 않게)
  - tracking lost → contact reset + debug publish
  - child facemesh 실패 → contact reset + debug publish
  - contact:
    - True면 `consec_contact += 1`, gaze_duration += dt
    - False면 `consec_contact = 0`

---

## 5. Debugging & Observability

### MJPEG stream
- `GET /debug/mjpeg` (FastAPI router: `app/rtn/service/debug_stream.py`)
- 분석 루프는 `FrameBroker.publish(frame)`로 최신 프레임만 유지 (`app/rtn/debug/broker.py`)

### Overlay 내용
- tracks bbox + id
- role assigned 여부
- parent/child label (P/C)
- parent ROI mask + convex hull
- child iris landmarks 점
- gaze ray (start→end)
- contact 상태/연속 프레임/dx dy

**Why this matters**
- “모델 성능”보다 먼저, 실패 케이스에서 원인을 즉시 찾는 게 팀 생산성을 좌우함  
  (role swap? mesh fail? ROI 이상? ray 방향 이상?)

---

## 6. Known Limitations (현재 한계)

1) **Role assignment가 area 기반**
   - 거리 역전, 프레임 내 얼굴 크기 변동에서 오판 가능
2) **FaceMesh/iris가 측면/가림/저해상도에서 실패 가능**
3) **2D gaze라서 head pose/카메라 왜곡에 취약**
4) **VAD가 ‘이름 부르기’ 특화가 아니라 speech 전체를 잡음**
   - 호명 검출(KWS/ASR)로 고도화 필요

---

## 7. Recording Guidelines (데이터 품질 가이드)

- 부모/아이 얼굴이 프레임 중앙에 잘 들어오게
- 조명 균일(눈 주변 그림자 최소)
- 얼굴 가림(손/장난감) 최소
- 가능한 정면에 가깝게, 측면이 심하면 mesh 실패 확률 증가
- 카메라 흔들림 최소(트래킹 안정성)

---

## 8. Roadmap (후속 계획)

### Short-term (안정화)
- role assignment 개선:
  - 위치 기반(화면 좌/우), 상호 위치 관계, 시간적 안정성 등 결합
- VAD → “호명” 특화:
  - 간단한 KWS 또는 ASR keyword match 도입

### Mid-term (정확도)
- head pose(3D) + gaze 결합:
  - 3D face pose 추정 + eye gaze를 결합해 contact 안정화
- 평가 프로토콜:
  - 라벨링 정의(성공/실패, latency 기준) + 테스트 클립 세트 고정

### Long-term (학습 기반)
- 도메인 데이터 확보 후 학습 gaze/contact classifier로 대체
- 오프라인 배치/큐 기반 비동기 처리(RabbitMQ/Celery)로 운영 확장

---

## 9. Repro / How to run
- `README.md` Quickstart 참고
- `/docs`에서 API 실행 가능
- `/debug/mjpeg`에서 프레임 디버그 가능
