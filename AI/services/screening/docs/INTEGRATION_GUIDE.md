# Screening AI 서비스 통합 가이드

## 개요

Screening AI 서비스는 **LiveKit WebRTC**를 통해 실시간 비디오/오디오 스트림을 분석하여 사전 검사(Preflight Screening)를 수행합니다.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  AI Server   │
│  (WebRTC)    │     │  (REST API)  │     │  (FastAPI)   │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                         │
       │         ┌──────────────┐                │
       └────────▶│   LiveKit    │◀───────────────┘
                 │   Server     │
                 └──────────────┘
```

---

## 1. Backend → AI: 스크리닝 분석 시작

- **Method**: `POST`
- **Endpoint**: `/api/v1/analysis/start`

### Request Body
```json
{
  "room_name": "screening_205285510064197279_92a9df5d",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "session_id": 205285510064197279,
  "participant_name": "ai-agent-5f3beae8-ab90-49dc"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `room_name` | String | LiveKit 방 이름 (필수) |
| `token` | String | AI용 LiveKit JWT 토큰 (필수) |
| `session_id` | Long | 세션 ID (로깅/추적용) |
| `participant_name` | String | AI 참가자 이름 |

### Response (200 OK)
```json
{
  "status": "started",
  "room_name": "screening_205285510064197279_92a9df5d",
  "message": "Analysis started successfully"
}
```

---

## 2. AI → Backend: 스크리닝 완료 알림

- **Method**: `POST`
- **Endpoint**: `/api/v1/screening/complete`

### Request Body
```json
{
  "roomName": "screening_205285510064197279_92a9df5d",
  "status": "success"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `roomName` | String | LiveKit 방 이름 (필수) |
| `status` | String | "success" 또는 "failure" |

---

## 3. AI → Frontend: DataChannel 메시지

### 3.1 실시간 가이드 (`guide`)

```json
{
  "type": "guide",
  "message": "가까이 오세요",
  "person_count": 2,
  "distance": 180,
  "timestamp": "2026-01-31T12:34:56",
  
  "_compat": {
    "flags": ["NOISE_HIGH"]
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `type` | String | `"guide"` |
| `message` | String | 사용자에게 보여줄 안내 메시지 |
| `person_count` | Integer | 현재 감지된 얼굴 수 |
| `distance` | Integer | 추정 거리 (cm), 가장 큰 얼굴(성인) 기준 |
| `timestamp` | String | ISO 8601 형식 |
| `_compat` | Object | **하위 호환 필드 (명세에 없음)** |

---

### 3.2 스크리닝 완료 (`screening_complete`)

```json
{
  "type": "screening_complete",
  "status": "success",
  "summary": {
    "total_frames": 1500,
    "valid_frames": 1200,
    "confidence": 0.80
  },
  "timestamp": "2026-01-31T12:35:00",
  
  "_compat": {
    "passed": true,
    "failure_reason": null,
    "flags": [],
    "ratios": {...},
    "scores": {...},
    "details": {}
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `type` | String | `"screening_complete"` |
| `status` | String | `"success"` 또는 `"failure"` |
| `summary.total_frames` | Integer | 분석된 총 프레임 수 |
| `summary.valid_frames` | Integer | 조건 만족한 프레임 수 |
| `summary.confidence` | Float | valid_frames / total_frames |
| `_compat` | Object | **하위 호환 필드 (명세에 없음)** |

---

### 3.3 에러 메시지 (`error`)

```json
{
  "type": "error",
  "message": "카메라를 찾을 수 없습니다",
  "code": "CAMERA_NOT_FOUND"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `type` | String | `"error"` |
| `message` | String | 에러 메시지 |
| `code` | String | 에러 코드 |

#### 에러 코드

| Code | 설명 |
|------|------|
| `INTERNAL_ERROR` | AI 서버 내부 오류 |
| `LIVEKIT_CONNECTION_FAILED` | LiveKit 연결 실패 |
| `TRACK_SUBSCRIPTION_FAILED` | 비디오/오디오 트랙 구독 실패 |
| `TIMEOUT` | 분석 타임아웃 |

---

### 3.4 Progress 메시지 (명세에 없음 - AI 확장)

> [!NOTE]
> 이 메시지 타입은 공식 API 명세에 없습니다.
> AI 서버에서 디버깅/분석 용도로 추가 제공합니다.

```json
{
  "type": "progress",
  "progress": 0.65,
  "ratios": {
    "two_faces_ratio": 1.0,
    "roi1_face_ratio": 1.0,
    "roi2_face_ratio": 1.0,
    "noise_high_ratio": 0.1,
    "low_light_ratio": 0.05
  },
  "scores": {
    "avg_rms_dbfs": -42.5,
    "avg_luma_mean": 125.3
  },
  "flags": [],
  "timestamp": "2026-01-31T12:34:56"
}
```

---

## 4. 하위 호환 필드 (`_compat`)

> [!IMPORTANT]
> 아래 필드들은 **공식 API 명세에 포함되지 않습니다.**
> AI 서버에서 디버깅/분석 용도로 추가 제공하는 확장 필드입니다.

| 메시지 타입 | 하위호환 필드 | 설명 |
|-------------|--------------|------|
| `guide` | `_compat.flags` | 현재 문제 플래그 목록 |
| `screening_complete` | `_compat.passed` | 통과 여부 |
| `screening_complete` | `_compat.failure_reason` | 실패 사유 |
| `screening_complete` | `_compat.flags` | 마지막 문제 플래그 |
| `screening_complete` | `_compat.ratios` | 품질 비율 지표 |
| `screening_complete` | `_compat.scores` | 품질 점수 지표 |
| `screening_complete` | `_compat.details` | 상세 디버그 정보 |
| `progress` | 전체 | 명세에 없는 메시지 타입 |

---

## 5. 전체 통신 플로우

```
1. 사용자가 프론트에서 "스크리닝 시작" 클릭
   ↓
2. 프론트 → 백엔드: POST /screening/start
   ↓
3. 백엔드 → AI: POST /analysis/start (비동기)
   ↓
4. AI → LiveKit: 방 접속 (token 사용)
   ↓
5. 프론트 → LiveKit: 방 접속 + 카메라 송출
   ↓
6. AI ↔ 프론트: 실시간 영상 분석 및 가이드 전송 (Data Channel)
   ↓
7. AI → 백엔드: POST /screening/complete
   ↓
8. 백엔드: Redis 상태 업데이트 (PENDING → READY)
   ↓
9. 프론트 → 백엔드: GET /screening/status (상태 확인)
```

---

## 6. 환경 변수 설정

AI Server `.env` 파일:
```env
LIVEKIT_URL=ws://localhost:7880     # LiveKit 서버 주소
BACKEND_URL=http://localhost:8080   # Backend 콜백 주소
```

| 환경 | 백엔드 URL | LiveKit URL |
|------|-----------|-------------|
| 로컬 개발 | `http://localhost:8080` | `ws://localhost:7880` |
| 배포 환경 | `https://api.your-domain.com` | `wss://livekit.your-domain.com` |

---

## 7. Frontend 구현 예시 (JavaScript)

```javascript
// LiveKit 룸 연결 후
room.on(RoomEvent.DataReceived, (payload, participant) => {
  const message = JSON.parse(new TextDecoder().decode(payload));
  
  switch (message.type) {
    case 'progress':
      // (선택) 진행 상황 표시
      updateProgressBar(message.progress);
      break;
      
    case 'guide':
      // 사용자 안내 메시지
      showGuideMessage(message.message);
      updatePersonCount(message.person_count);
      updateDistance(message.distance);
      break;
      
    case 'screening_complete':
      // 스크리닝 완료
      if (message.status === 'success') {
        onScreeningPassed();
      } else {
        onScreeningFailed();
      }
      console.log('Total frames:', message.summary.total_frames);
      console.log('Valid frames:', message.summary.valid_frames);
      console.log('Confidence:', message.summary.confidence);
      break;
      
    case 'error':
      // 에러 처리
      showError(message.message, message.code);
      break;
  }
});
```

---

## 8. 서버 실행

```bash
cd AI/services/screening
uvicorn src.serving.app:app --host 0.0.0.0 --port 8001
```

---

## 9. API 엔드포인트 요약

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/analysis/start` | 분석 시작 |
| `GET` | `/api/v1/analysis/active` | 활성 세션 목록 |
| `GET` | `/health` | 헬스체크 |
| `GET` | `/admin/stats/failures` | 실패 통계 |
| `GET` | `/admin/stats/latency` | 지연시간 통계 |
