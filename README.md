<div align="center">

<img src="./docs/logo.svg" width="100"/>

# AITIME

### 자폐 진단 디지털의료기기<br/>
> 12-23개월 영유아와 부모가, 가정 내에서 수행하는 표준화된 4가지 과제를, AI가 채점하여, 소아과 의사의 초진 면담/ 관찰 과정을 대체하는, 디지털 의료기기입니다.

<br/>

![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/Frontend-TypeScript-3178C6?logo=typescript&logoColor=white)
![SpringBoot](https://img.shields.io/badge/Backend-SpringBoot-6DB33F?logo=springboot&logoColor=white)
![AI](https://img.shields.io/badge/AI-Multimodal-8A2BE2)
![Docker](https://img.shields.io/badge/Infra-Docker-2496ED?logo=docker&logoColor=white)
![AWS](https://img.shields.io/badge/Cloud-AWS-FF9900?logo=amazonaws&logoColor=white)

</div>

---

<br/>

# ✨ Why AITIME?

자폐 진단은 짧은 시간 동안  
다양한 행동 신호를 종합해 판단해야 하는 과정입니다.

AITIME은 그 관찰 과정을  
**AI 기반 정량 데이터**로 변환합니다.

- 반응 시간(ms)
- 모방 정확도
- 시선 지속 시간
- 음성 반응 여부
- 행동 성공률

의사는 더 이상 기억에 의존하지 않습니다.  
이미 데이터가 정리되어 있습니다.

---

<br/>


# 🧠 System Architecture

<img src="./docs/architecture.png" width="100%" />

<details>
  <summary><b>📌 Mermaid로 자세히 보기 (Click)</b></summary>

```mermaid
flowchart TD
    %% Client Tier
    Client((🌐 Client<br/>Web/Mobile App))

    %% Infrastructure / CI/CD
    subgraph Infra [인프라 및 CI/CD]
        AWS[AWS 인프라]
        Docker[Docker 컨테이너]
        Jenkins[Jenkins CI/CD]
    end

    %% Application & Communication Tier
    subgraph AppTier [애플리케이션 프론트/백엔드]
        Nginx[Nginx]
        NodeJS[Node.js<br/>Frontend]
        SpringBoot[Spring Boot<br/>Backend API]
    end

    %% Pre-flight Tier
    subgraph PreflightTier [프리플라이트 스크리닝 - 실시간]
        LiveKit[🎥 LiveKit<br/>WebRTC Server]
        PreflightAI[🤖 Pre-flight AI<br/>실시간 스크리닝]
    end

    %% Main Analysis Tier
    subgraph MainAnalysisTier [본 영상 분석 파이프라인 - 비동기]
        MQ_Job[🐰 RabbitMQ<br/>Job Queue]
        
        %% 4개의 서로 다른 AI 명시
        subgraph AIs [독립된 4개의 AI 분석 모델]
            direction LR
            AI_Motion[🤖 AI: 동작 모방]
            AI_Speech[🤖 AI: 발화 모방]
            AI_Face[🤖 AI: 대면 호명]
            AI_NonFace[🤖 AI: 비대면 호명]
        end
        
        MQ_Result[🐰 RabbitMQ<br/>Job Results]
    end

    %% Data & Storage
    subgraph DataTier [데이터베이스 및 스토리지]
        Redis[(🔴 Redis<br/>Session/Cache)]
        MySQL[(🐬 MySQL<br/>RDBMS)]
        MINio[(🪿 MINio<br/>Object Storage)]
    end

    %% ==========================================
    %% 릴레이션 (데이터 및 제어 흐름)
    %% ==========================================

    %% 1~4. 기존 라우팅 및 LiveKit 연결
    Client -->|HTTP/HTTPS| Nginx
    Nginx --> NodeJS
    
    Client -.->|1. 방 입장 요청| NodeJS
    NodeJS -.->|2. 요청 전달| SpringBoot
    SpringBoot -.->|3. 방 생성 및 토큰 발급| LiveKit
    SpringBoot -->|4. AI용 토큰 및 지시| PreflightAI
    
    Client <-->|5. WebRTC 직접 연결| LiveKit
    PreflightAI <-->|6. WebRTC 직접 연결| LiveKit

    %% 5. 영상 업로드 (프론트 -> MINio)
    NodeJS -.->|7. 업로드 URL 요청| SpringBoot
    SpringBoot -.->|8. Presigned URL 반환| NodeJS
    NodeJS -->|9. 영상 파일 업로드| MINio

    %% 6. 비동기 AI 분석 흐름 (4개의 개별 AI로 분기)
    SpringBoot -->|10. 분석 메세지 발행| MQ_Job
    
    %% RabbitMQ에서 각각의 AI로 라우팅
    MQ_Job -->|작업 할당| AI_Motion
    MQ_Job -->|작업 할당| AI_Speech
    MQ_Job -->|작업 할당| AI_Face
    MQ_Job -->|작업 할당| AI_NonFace
    
    %% 각 AI가 MINio에서 영상을 다운로드
    MINio -.->|영상 다운로드| AI_Motion
    MINio -.->|영상 다운로드| AI_Speech
    MINio -.->|영상 다운로드| AI_Face
    MINio -.->|영상 다운로드| AI_NonFace

    %% 각 AI의 분석 결과 취합
    AI_Motion -->|결과 전달| MQ_Result
    AI_Speech -->|결과 전달| MQ_Result
    AI_Face -->|결과 전달| MQ_Result
    AI_NonFace -->|결과 전달| MQ_Result
    
    MQ_Result -->|11. 최종 결과 수신 및 DB 저장| SpringBoot

    %% 7. DB 연결
    SpringBoot -.-> MySQL
    SpringBoot -.-> Redis
```
</details> <br/>

---

# 🎥 Demo Experience

## 1. 로그인

<img src="./docs/gif/로그인.gif" width="100%" />

---

## 2. 자녀 선택

<img src="./docs/gif/자녀초기화면.gif" width="100%" />

---

## 3. 자녀 추가

<img src="./docs/gif/자녀추가.gif" width="100%" />

---

## 4. 자녀 초대코드 등록

<img src="./docs/gif/자녀초대코드등록.gif" width="100%" />

---

## 5. 검사 사전 동의

<img src="./docs/gif/검사사전동의.gif" width="100%" />

---

## 6. 동작 모방

<img src="./docs/gif/동작모방.gif" width="100%" />

---

## 7. 발화 모방

<img src="./docs/gif/발화모방.gif" width="100%" />

---

## 8. 대면 호명

<img src="./docs/gif/대면호명.gif" width="100%" />

---

## 9. 비대면 호명

<img src="./docs/gif/비대면호명.gif" width="100%" />

---

## 10. 검사 영상 조회

<img src="./docs/gif/검사영상조회.gif" width="100%" />

---

## 11. 검사 제출

<img src="./docs/gif/검사제출.gif" width="100%" />

---

## 12. 의사 환자 조회

<img src="./docs/gif/의사환자조회.gif" width="100%" />

---

## 13. 의사 차트 확인

<img src="./docs/gif/의사 차트 확인.gif" width="100%" />

---

## 14. 타임스탬프 선택

<img src="./docs/gif/타임스탬프 선택.gif" width="100%" />

---

## 15. 진단 결과 추가

<img src="./docs/gif/진료추가.gif" width="100%" />

---

## 16. 접수처 로그인

<img src="./docs/gif/접수처로그인.gif" width="100%" />

---

## 17. 접수처 초대코드 발급

<img src="./docs/gif/초대코드발급.gif" width="100%" />

<br/>

# 🏗 Tech Stack

### Frontend
- React
- TypeScript
- Zustand
- TanStack Query
- TailwindCSS
- Vite

### Backend
- Spring Boot 3
- Spring Security
- JWT
- JPA
- Redis
- RabbitMQ
- WebSocket(Livekit)

### AI
- PyTorch
- OpenCV
- RT-DETR
- ViTPose
- Faster-Whisper
- Pyannote
- DTW 기반 행동 정렬

### Infra
- AWS EC2
- Docker / Docker Compose
- Nginx Reverse Proxy
- Jenkins CD

---

<br/>

# 👥 Team

<div align="center">

<table>
<tr>

<td align="center" width="200">

<a href="https://github.com/dobby0628">
<img src="https://avatars.githubusercontent.com/dobby0628" width="120" style="border-radius: 50%;" />
</a>

<br/>

<b>조수진</b>  
PM / Infra / BE

<br/>
<a href="https://github.com/dobby0628">GitHub →</a>

</td>

<td align="center" width="200">

<a href="https://github.com/hyoseok8948">
<img src="https://avatars.githubusercontent.com/hyoseok8948" width="120" style="border-radius: 50%;" />
</a>

<br/>

<b>김효석</b>  
UI/UX / FE

<br/>
<a href="https://github.com/hyoseok8948">GitHub →</a>

</td>

<td align="center" width="200">

<a href="https://github.com/najung-h">
<img src="https://avatars.githubusercontent.com/najung-h" width="120" style="border-radius: 50%;" />
</a>

<br/>

<b>나정현</b>  
AI

<br/>
<a href="https://github.com/najung-h">GitHub →</a>

</td>

</tr>

<tr>

<td align="center">

<a href="http://github.com/DonghanPark">
<img src="https://avatars.githubusercontent.com/DonghanPark" width="120" style="border-radius: 50%;" />
</a>

<br/>

<b>박동한</b>  
AI

<br/>
<a href="http://github.com/DonghanPark">GitHub →</a>

</td>

<td align="center">

<a href="https://github.com/pyy2114">
<img src="https://avatars.githubusercontent.com/pyy2114" width="120" style="border-radius: 50%;" />
</a>

<br/>

<b>박윤영</b>  
Backend / DB  

<br/>
<a href="https://github.com/pyy2114">GitHub →</a>

</td>

<td align="center">

<a href="https://github.com/ohjisu320">
<img src="https://avatars.githubusercontent.com/ohjisu320" width="120" style="border-radius: 50%;" />
</a>

<br/>

<b>오지수</b>  
UI/UX / FE

<br/>
<a href="https://github.com/ohjisu320">GitHub →</a>
</a>

</td>

</tr>
</table>

</div>

---

<br/>

# 🎯 Impact

- 진단 보조 객관 지표 제공
- 의료진 판단 강화
- 대기 시간 단축 가능성
- 재검토 가능한 디지털 기록 생성
- 확장 가능한 AI 기반 구조

---

<div align="center">

## AITIME

의사의 경험을 대체하지 않습니다.  
의사의 판단을 강화합니다.

</div>