
# face to face name response model

호명(부모 발화) 이후 **아이가 부모의 눈 영역을 바라보는지**를 동영상에서 추정하는 모델

- 입력: 동영상(mp4/mov/avi/mkv/webm)
- 출력: 시도별 성공 여부/지연 시간/시선 유지 시간 + 요약 지표(JSON)
- 제공: FastAPI 서비스 + MJPEG 디버그 스트림

---

## What’s inside

### Endpoints
- `GET /docs` : Swagger UI
- `GET /health` : health check
- `POST /analyze` : 서버 로컬 경로 영상 분석(JSON body)
- `POST /analyze/upload` : 파일 업로드 분석(multipart)
- `GET /debug/mjpeg` : 최신 디버그 프레임 MJPEG 스트림(브라우저로 확인)

### Output Metrics (핵심 지표)
- `success_count / total_call_count`
- `avg_latency_s` : call_end 이후 첫 eye-contact까지 평균 지연
- `total_gaze_duration_s` : eye-contact 유지 시간 총합

---

## Architecture (Service + Model Pipeline)

```mermaid
flowchart LR
  %% =========================
  %% Styles
  %% =========================
  classDef api fill:#EEF7FF,stroke:#2B6CB0,stroke-width:1px,color:#1A365D;
  classDef core fill:#F7FAFC,stroke:#4A5568,stroke-width:1px,color:#2D3748;
  classDef vision fill:#F0FFF4,stroke:#2F855A,stroke-width:1px,color:#22543D;
  classDef debug fill:#FFFAF0,stroke:#B7791F,stroke-width:1px,color:#744210;

  %% =========================
  %% API
  %% =========================
  subgraph S1["API"]
    A[Client] -->|POST /analyze/upload| B["FastAPI<br/>app/main.py"]
  end
  class A,B api;

  %% =========================
  %% Core pipeline
  %% =========================
  subgraph S2["Core Pipeline"]
    B -->|save tmp video| C[VideoAnalyzer]
    C --> D["VAD: Silero<br/>(audio segments)"]
    D --> E["Loop: per call segment"]
    E --> F["WindowAnalyzer<br/>call_end → call_end + window_s"]
  end
  class C,D,E,F core;

  %% =========================
  %% Vision (per window)
  %% =========================
  subgraph S3["Vision (per window)"]
    F --> G["Face Detect<br/>(MediaPipe)"]
    G --> H["Tracking<br/>(SORT)"]
    H --> I["Role Assign<br/>(Area warmup)"]

    I --> J["Child: FaceMesh + Iris"]
    I --> K["Parent ROI<br/>(mesh or bbox fallback)"]

    J --> L["2D Gaze Ray"]
    K --> M["Raycast Contact"]
    M --> N["Result JSON<br/>per_call + summary"]
  end
  class G,H,I,J,K,L,M,N vision;

  %% =========================
  %% Debug stream
  %% =========================
  subgraph S4["Debug Stream"]
    F --> O["Debug Renderer"]
    O -->|publish latest frame| P[FrameBroker]
    P -->|GET /debug/mjpeg| Q[Browser]
  end
  class O,P,Q debug;

````

---

## Quickstart (Local)

### 0) Prerequisites

* Python 3.11
* **ffmpeg** (VAD 단계에서 오디오 추출에 필요)

  * macOS: `brew install ffmpeg`
  * Ubuntu: `sudo apt-get install -y ffmpeg`

### 1) Create env & install

```bash
# repo root 기준
conda env create -f app/environment.yml
conda activate face_to_face_name_response
pip install -r app/requirements.txt
```

> 참고: `requirements.txt`는 CUDA 12.6 torch wheel을 사용합니다.

### 2) Run server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

* Swagger: `http://localhost:8005/docs`
* Debug MJPEG: `http://localhost:8005/debug/mjpeg`

---

## Quickstart (Docker)

Docker는 ffmpeg가 포함되어 있습니다.

```bash
docker build -t rtn-eyecontact -f app/Dockerfile .
docker run -p 8000:8000 rtn-eyecontact
# http://localhost:8000/docs
# http://localhost:8000/debug/mjpeg
```

---

## API Examples

### 1) Upload analyze

```bash
curl -X POST "http://localhost:8005/analyze/upload" \
  -H "accept: application/json" \
  -F "file=@sample.mp4"
```

### 2) Local path analyze

```bash
curl -X POST "http://localhost:8005/analyze" \
  -H "content-type: application/json" \
  -d '{"video_path":"/absolute/path/to/sample.mp4"}'
```

### Example response shape

```json
{
  "video": "sample.mp4",
  "params": {
    "window_s": 5.0,
    "vad_merge_gap_s": 0.3,
    "vad_min_speech_ms": 250,
    "vad_min_silence_ms": 250,
    "min_contact_frames": 3,
    "warmup_s": 1.0,
    "face_det_conf_th": 0.6
  },
  "summary": {
    "success_count": 4,
    "total_call_count": 5,
    "avg_latency_s": 1.45,
    "total_gaze_duration_s": 0.93
  },
  "per_call": [
    {
      "call_index": 1,
      "call_start_s": 0.00,
      "call_end_s": 0.67,
      "success": false,
      "latency_s": null,
      "gaze_duration_s": 0.0
    }
  ]
}
```

---

## Configuration (튜닝 포인트)

서비스 생성 시 `build_engine()` 파라미터로 조절합니다.

* 위치: `app/rtn/service/engine.py` / 사용: `app/main.py`
* 주요 파라미터:

  * `window_s` : call_end 이후 관찰 윈도우(기본 5초)
  * `conf` : face detection confidence threshold(기본 0.6)
  * `warmup_s` : role assignment warmup(기본 1초)
  * `min_contact_frames` : 성공 판정 연속 프레임 수(기본 3)
  * `enable_mjpeg`, `jpeg_quality` : 디버그 스트림 on/off 및 품질

---

## Docs

* 모델/알고리즘 상세: `./docs/model_baseline.md`

---