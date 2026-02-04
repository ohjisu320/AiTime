# 📋 닥터 대시보드 - 필요 API 명세 (백엔드 요청용)

> **작성일**: 2026-02-04  
> **작성자**: 프론트엔드 팀

---

## 1. 오늘 예약 환자 대기열 조회

### 요청
```
GET /doctor/waiting-list?date=2026-02-04
Authorization: Bearer {accessToken}
```

### 응답
```json
{
  "code": 200,
  "data": [
    {
      "childId": "uuid",
      "userId": "uuid",
      "name": "홍길동",
      "gender": "MALE",
      "monthlyAge": 48,
      "birthdate": "2022-03-15",
      "latestExamStatus": "COMPLETED"
    }
  ]
}
```

---

## 2. ADOS-2 검사 결과 조회

환자의 ADOS-2 검사 항목별 점수 조회

### 요청
```
GET /exams/{examId}/ados-result
Authorization: Bearer {accessToken}
```

### 응답
```json
{
  "code": 200,
  "data": {
    "examId": "uuid",
    "childId": "uuid",
    "examDate": "2026-02-04",
    "module": "MODULE_1",
    "categories": [
      {
        "title": "A. 언어 및 의사소통",
        "items": [
          { "code": "A1", "name": "전반적 언어 수준", "score": 2, "maxScore": 3 },
          { "code": "A2", "name": "말의 비정상적 억양", "score": 1, "maxScore": 2 }
        ],
        "subtotal": 3
      },
      {
        "title": "B. 상호적 사회 상호작용",
        "items": [
          { "code": "B1", "name": "눈맞춤", "score": 2, "maxScore": 2 },
          { "code": "B2", "name": "표정", "score": 1, "maxScore": 2 }
        ],
        "subtotal": 3
      }
    ],
    "totalScore": 12,
    "cutoffScore": 7,
    "classification": "AUTISM"
  }
}
```

**`classification` enum:**
- `AUTISM` - 자폐
- `AUTISM_SPECTRUM` - 자폐 스펙트럼
- `NON_SPECTRUM` - 비스펙트럼

---

## 3. AI 진단 판정 결과 조회

AI 모델의 진단 결과, 근거, 상세 설명

### 요청
```
GET /exams/{examId}/ai-diagnosis
Authorization: Bearer {accessToken}
```

### 응답
```json
{
  "code": 200,
  "data": {
    "examId": "uuid",
    "riskLevel": "HIGH",
    "riskScore": 78.5,
    "diagnosis": "자폐 스펙트럼 장애 고위험군",
    "confidence": 0.85,
    "reasoning": [
      "눈맞춤 회피 빈도가 정상 범위 대비 2.3배 높음",
      "반복 행동 패턴 12회 관찰 (평균 3회)",
      "사회적 상호작용 시도 횟수 현저히 낮음"
    ],
    "detailedDescription": "환자는 검사 중 일관된 눈맞춤 회피를 보였으며, 손 흔들기 등 상동행동이 빈번하게 관찰되었습니다. 부모 호명에 대한 반응 지연이 현저하며, 또래 상호작용에서 어려움이 예상됩니다.",
    "recommendation": "정밀 진단 및 조기 개입 프로그램 권장"
  }
}
```

**`riskLevel` enum:**
- `HIGH` - 고위험
- `MEDIUM` - 중위험  
- `LOW` - 저위험

---

## 4. 트렌드 차트 데이터 조회

환자의 날짜별 AI 검사 점수 이력

### 요청
```
GET /children/{childId}/exam-history
Authorization: Bearer {accessToken}
```

### 응답
```json
{
  "code": 200,
  "data": {
    "childId": "uuid",
    "examHistory": [
      {
        "examId": "uuid-1",
        "examDate": "2025-11-15",
        "aiScore": 65.2,
        "adosTotal": 10,
        "classification": "AUTISM_SPECTRUM"
      },
      {
        "examId": "uuid-2",
        "examDate": "2026-01-20",
        "aiScore": 72.8,
        "adosTotal": 11,
        "classification": "AUTISM_SPECTRUM"
      },
      {
        "examId": "uuid-3",
        "examDate": "2026-02-04",
        "aiScore": 78.5,
        "adosTotal": 12,
        "classification": "AUTISM"
      }
    ]
  }
}
```

---

## 5. 세션별 영상 목록 조회

환자의 검사 세션별 영상 목록

### 요청
```
GET /children/{childId}/sessions
Authorization: Bearer {accessToken}
```

### 응답
```json
{
  "code": 200,
  "data": [
    {
      "sessionId": "uuid-1",
      "examId": "uuid",
      "sessionDate": "2026-02-04",
      "sessionType": "ADOS_MODULE_1",
      "videoUrl": "https://storage.example.com/videos/session-1.mp4",
      "thumbnailUrl": "https://storage.example.com/thumbnails/session-1.jpg",
      "duration": 180,
      "status": "ANALYZED"
    },
    {
      "sessionId": "uuid-2",
      "examId": "uuid",
      "sessionDate": "2026-01-20",
      "sessionType": "FREE_PLAY",
      "videoUrl": "https://storage.example.com/videos/session-2.mp4",
      "thumbnailUrl": "https://storage.example.com/thumbnails/session-2.jpg",
      "duration": 240,
      "status": "ANALYZED"
    }
  ]
}
```

**`status` enum:**
- `PENDING` - 분석 대기
- `ANALYZING` - 분석 중
- `ANALYZED` - 분석 완료
- `FAILED` - 분석 실패

---

## 6. 영상 분석 결과 조회

특정 세션의 AI 영상 분석 결과 (타임스탬프 포함)

### 요청
```
GET /sessions/{sessionId}/analysis
Authorization: Bearer {accessToken}
```

### 응답
```json
{
  "code": 200,
  "data": {
    "sessionId": "uuid",
    "videoUrl": "https://storage.example.com/videos/session-1.mp4",
    "totalDuration": 180,
    "timestamps": [
      {
        "id": 1,
        "type": "parent",
        "label": "호명 시도",
        "startTime": 5,
        "duration": 3
      },
      {
        "id": 2,
        "type": "child-vocal",
        "label": "옹알이",
        "startTime": 12,
        "duration": 4
      },
      {
        "id": 3,
        "type": "child-behavior",
        "label": "손 흔들기",
        "startTime": 25,
        "duration": 5
      }
    ]
  }
}
```

---

## 7. 임상의 종합 소견 저장

의사의 종합 소견 메모 저장

### 요청
```
POST /exams/{examId}/clinical-notes
Authorization: Bearer {accessToken}
Content-Type: application/json

{
  "note": "환자는 전반적으로 자폐 스펙트럼 장애 기준에 부합하는 행동 패턴을 보이며, 조기 개입이 필요합니다.",
  "recommendation": "언어치료 및 ABA 치료 권장"
}
```

### 응답
```json
{
  "code": 201,
  "message": "저장 성공",
  "data": {
    "noteId": "uuid",
    "examId": "uuid",
    "createdAt": "2026-02-04T11:25:00Z"
  }
}
```

---

## 📝 우선순위

| 순위 | API | 이유 |
|-----|-----|------|
| 1 | `/exams/{examId}/ados-result` | ADOS-2 결과 패널 필수 |
| 2 | `/exams/{examId}/ai-diagnosis` | AI 진단 패널 필수 |
| 3 | `/children/{childId}/sessions` | 세션 목록 표시 필수 |
| 4 | `/sessions/{sessionId}/analysis` | 영상 선택 시 타임라인 표시 |
| 5 | `/children/{childId}/exam-history` | 트렌드 차트 표시 |
| 6 | `/exams/{examId}/clinical-notes` | 저장하기 버튼 기능 |

---

## 📊 닥터 대시보드 API 연결 현황

### ✅ 연결 완료

| API | 엔드포인트 | 사용 위치 |
|-----|-----------|----------|
| 환자 검색 | `GET /doctor/patients` | `useDoctorDashboard.ts` - 대기열 조회 |
| 병원직원 로그아웃 | `POST /hospital-staff/logout` | `PatientDetailPanel.tsx` - 로그아웃 버튼 |

### ❌ 연결 필요 (백엔드 개발 필요)

| 기능 | 필요 API | 현재 상태 |
|-----|----------|----------|
| ADOS-2 결과 | `GET /exams/{examId}/ados-result` | 더미 데이터 |
| AI 진단 판정 | `GET /exams/{examId}/ai-diagnosis` | 더미 데이터 |
| 세션 영상 목록 | `GET /children/{childId}/sessions` | 더미 데이터 |
| 영상 분석 결과 | `GET /sessions/{sessionId}/analysis` | 더미 데이터 |
| 트렌드 차트 | `GET /children/{childId}/exam-history` | 더미 데이터 |
| 소견 저장 | `POST /exams/{examId}/clinical-notes` | 미구현 |

### 🔄 더미 데이터 위치

| 파일 | 더미 데이터 |
|-----|-----------|
| `doctorApi.ts` | `DUMMY_DATA` - 환자 상세 정보 (height, weight 등) |
| `DoctorDashboardPage.tsx` | `MOCK_ANALYSIS` - 영상 분석 타임스탬프 |
| `AiDiagnosisPanel.tsx` | ADOS 항목, AI 진단 결과 |
| `TrendChartPanel.tsx` | 차트 데이터 |
| `SessionListPanel.tsx` | 세션 목록 |
