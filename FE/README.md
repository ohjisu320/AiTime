# 🧠 AiTime — 프론트엔드

> 프론트엔드 레포지토리입니다.

---

## 📌 기술 스택

| 분류 | 기술 |
|------|------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite 6 |
| Styling | TailwindCSS v4 + SCSS |
| 상태 관리 | TanStack Query v5 |
| UI 라이브러리 | Radix UI + shadcn/ui |
| 라우팅 | React Router v7 |
| HTTP 클라이언트 | Axios |
| 애니메이션 | Motion (Framer Motion) |

---

## 📁 프로젝트 구조

```
src/
├── api/             # Axios 인스턴스, 인터셉터, 공통 타입
├── app/             # 라우터, 앱 진입점
├── components/      # 공통 UI 컴포넌트
├── domains/         # 도메인별 비즈니스 로직
│   ├── exam/        # 검사 플로우 (스크리닝, 녹화, 미션)
│   └── video/       # 영상 녹화 및 업로드
├── features/        # 페이지/기능 단위 조합
│   ├── auth/        # 로그인, 회원가입
│   ├── desk/        # 데스크 대시보드
│   ├── doctor/      # 의사 대시보드 (AI 분석, 타임라인)
│   ├── exam/        # 검사 플로우 페이지
│   └── parent/      # 보호자 플로우
├── hooks/           # 전역 공통 훅 (usePWAInstall 등)
└── styles/          # 전역 CSS, 테마 변수
```

---

## 🚀 핵심 기술 구현

### 1. PWA (Progressive Web App)

`vite-plugin-pwa` + 커스텀 `usePWAInstall` 훅을 통해 네이티브 앱 수준의 설치 경험을 제공합니다.

- **Android**: `beforeinstallprompt` 이벤트를 캡처하여 앱 내 커스텀 설치 버튼으로 트리거
- **iOS**: `navigator.standalone` 감지 후 수동 설치 안내 분기 처리
- `registerType: 'autoUpdate'` 기반 Service Worker 자동 갱신
- Workbox 최대 캐시 파일 크기 5MB 설정

```
src/hooks/usePWAInstall.ts   — 설치 가능 여부, iOS 분기, standalone 감지
vite.config.ts               — manifest, 아이콘, theme_color 설정
```

---

### 2. LiveKit 기반 실시간 AI 스크리닝

LiveKit SFU(Selective Forwarding Unit) 서버를 통해 AI 에이전트와 실시간으로 통신하며 검사 환경 스크리닝을 진행합니다.

**연결 플로우**
```
카메라/마이크 획득 (로컬 Preview 즉시 표시)
→ 백엔드 API로 세션 발급 (LiveKit Token)
→ LiveKit Room 연결 (최대 3회 자동 재시도)
→ AI 에이전트가 Participant로 Room 입장
→ DataChannel로 실시간 가이드 메시지 수신
→ 사람 수 감지(person_count) 기반 스크리닝 통과 판정
```

- AI 에이전트(`ai-agent-*`)의 Room 입장을 감지하여 스크리닝 상태 전환
- 연결 실패 시 1초 간격으로 최대 3회 재시도
- STUN 서버 명시적 설정으로 NAT 환경 대응

```
src/domains/exam/hooks/useLiveKitScreening.ts
```

---

### 3. Web Audio API 기반 실시간 dBFS 음량 측정

LiveKit의 오디오 트랙을 **별도의 Web Audio API 파이프라인**으로 분석하여 실시간 음량 게이지를 직접 구현했습니다.

> 초기에는 AI 서버에서 DataChannel로 볼륨 값을 수신하는 방식이었으나, 세 가지 이유로 클라이언트 로컬 분석으로 교체했습니다.
> - **레이턴시**: 네트워크 왕복 없이 즉시 반응하는 실시간 게이지 필요
> - **서버 독립성**: AI 서버 연결 이전 단계에서도 음량 게이지 표시 필요
> - **커스텀 임계값**: -35dB 소음 경계를 직접 정의하기 위해 원시 오디오 데이터 접근 필요

```ts
// RMS → dBFS → 0~100 볼륨 게이지 매핑
analyser.getFloatTimeDomainData(dataArray);
const rms = Math.sqrt(sumSquares / bufferLength);
const db = rms > 0 ? 20 * Math.log10(rms) : MIN_DB;

// -80dB ~ -35dB → 0 ~ 30  (조용한 환경)
// -35dB ~ 0dB   → 30 ~ 100 (소음 감지)
```

- `ScriptProcessorNode`로 오디오 버퍼 실시간 분석
- **-35dB**를 소음 경계 임계값으로 설정하여 검사 환경 품질 검증
- `smoothingTimeConstant: 0.3`으로 빠른 응답성 확보

```
src/domains/exam/hooks/useLiveKitScreening.ts — startScreening() 내부
```

---
### 4. MinIO Presigned URL 영상 업로드

검사 중 녹화된 영상을 S3 호환 오브젝트 스토리지(MinIO)에 3단계 파이프라인으로 업로드합니다.

| 단계 | 담당 | 내용 |
|------|------|------|
| ① Presigned URL 발급 | **BE** | MinIO 서명 URL 생성 → `uploadUrl`, `videoId`, `s3Key` 반환 |
| ② MinIO 직접 PUT 업로드 | **FE** | 백엔드를 우회하여 MinIO에 직접 바이너리 업로드 |
| ③ 업로드 완료 알림 | **FE → BE** | `s3Key` 전달하여 완료 알림 → BE가 AI 분석 파이프라인 트리거 |

**FE 핵심 처리 사항**
- ② 단계에서 Axios 인터셉터가 자동으로 붙이는 `Authorization` 헤더를 `transformRequest`로 명시적 제거 (MinIO 요구사항)
- `onUploadProgress` 콜백으로 실시간 업로드 진행률 추적
- 업로드 실패 시 1초 간격으로 최대 3회 자동 재시도
- `MediaRecorder` MimeType fallback: `video/mp4;h264 → video/webm;vp9` (Safari/Chrome 크로스 브라우저 대응)

```
src/domains/video/api/videoApi.ts
src/domains/video/hooks/useExamUpload.ts
src/domains/video/hooks/useMediaRecorder.ts
```


---

### 5. JWT Silent Refresh — 경쟁 조건 해결

Axios Response Interceptor에서 401 발생 시 토큰 갱신 중 동시 요청이 쏟아지는 **Race Condition** 문제를 Queue 패턴으로 해결했습니다.

- 첫 번째 401 요청이 토큰 갱신을 시작하는 동안, 이후 401 요청들은 `failedQueue`에 대기
- 갱신 완료 후 Queue를 일괄 처리하여 재요청
- 사용자 역할(일반 사용자 / 병원 스태프)에 따라 refresh 엔드포인트 동적 분기
- refreshToken은 HttpOnly Cookie로만 관리 (`withCredentials: true`)

```
src/api/axiosConfig.ts
```

---

### 6. 검사 이탈 방지 이중 가드

검사 진행 중 실수로 인한 데이터 손실을 방지하기 위해 브라우저 및 SPA 라우터 두 레벨에서 이탈을 차단합니다.

- **브라우저 레벨**: `beforeunload` 이벤트로 새로고침/탭 닫기 방지
- **SPA 레벨**: React Router `useBlocker`로 내부 라우팅 이탈 방지
- **직접 URL 접근 차단**: `location.state.verified` 유무로 스크리닝 미통과 상태에서 검사 페이지 직접 접근 차단

```
src/features/exam/pages/ExamPage.tsx
```

---

### 7. 다중 패널 플렉스 레이아웃(Flex Layout)

1-1.실제 병원에서 사용하는 EMR 서비스의 형태를 제공하기 위해 여러 컴포넌트를 한 화면 안에 배치할 수 있는 플렉스 레이아웃을 사용했습니다.
- Windows 테마 커스텀: .flexlayout__tabset, .flexlayout__splitter 등의 내부 클래스를 오버라이드하여 지정된 레트로(Windows 98 스타일) 색상 및 UI 테마를 강제로 적용합니다.

1-2.역할별로 잘게 쪼개진 9개의 하위 컴포넌트로 구성되어 있으며 크게 레이아웃(1개),패널(6개),모달(2개)로 이루어져 있습니다.
- 레이아웃 초기화 (DoctorLayout.tsx) : 레이아웃을 row 기반으로 분할하여 왼쪽부터 순서대로 '환자 대기열', '환자 정보', '영상 목록', '영상 분석(다중 가중치)', '트렌드/AI진단(우측 분할 컬럼)'을 배치합니다
.
1-3.각각의 컴포넌트는 화면 비율을 유지하면서 상하 , 좌우로 크기 조절이 가능하며, 사용자가 원하는 데로 배치가 가능합니다.
- Factory 패턴 렌더링: node.getComponent() 반환 키와 의사 대시보드에서 주입한 panels 객체를 매핑하여 탭 뷰에 리액트 노드를 동적으로 렌더링합니다.
- 마우스 핸들링: ResizeHandle 컴포넌트 사이의 드래그(mousemove, mouseup) 이벤트에 따라 마우스 Y좌표 이동량(deltaRatio)을 추적하여 인접한 상한단 레이아웃의 비율을 상쇄교환하는 방식으로 유연하게 동작합니다.

---

### 8. 영상 데이터 로딩

2-1. AI가 분석한 영상 데이터를 의사 대시보드에서 이중 로딩을 통해 초기 렌더링 속도와 안정성을 확보했습니다.
- 1순위(통합API) : /initial 엔드포인트를 호출해 검사 이력, 비디오, 그래프 데이터를 한번에 가져와 렌더링 부하를 최소화 했습니다.
- 2순위(개별) : S3 인증 오류 등 통합 API 호출 실패 시 에러를 캐치하고 상세 내역을 각각 분리된 API로 개별 요청하여 부분 장애에 대응합니다.

2-2. 비디오와 타임라인의 동기화를 통해 타임라임 선택시 영상에서 해당 시간으로 넘어가능 기능을 구현했습니다.
-  CentralAnalysis 내 <video controls>의 onTimeUpdate 이벤트를 리스닝하여 currentTime 상태를 밀리초 단위로 지속 갱신하며, 이를 타임라인에 전파합니다.

---
## ⚙️ 환경 설정

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
```

**환경 변수** (`.env.development` / `.env.production`)

```env
VITE_API_BASE_URL=       # 백엔드 API 기본 URL
VITE_LIVEKIT_URL=        # LiveKit 서버 WebSocket URL
```
