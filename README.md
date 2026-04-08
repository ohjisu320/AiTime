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

<img src="./docs/architecture.png" width="80%" />

<details>
  <summary><b>📌 Mermaid로 자세히 보기 (Click)</b></summary>
  <img src="./docs/mermaid.png" width="80%" />

</details> <br/>

---

# 🎥 Demo Experience

## 1. 로그인

<img src="./docs/gif/로그인.gif" width="80%" />

---

## 2. 자녀 선택

<img src="./docs/gif/자녀초기화면.gif" width="80%" />

---

## 3. 자녀 추가

<img src="./docs/gif/자녀추가.gif" width="80%" />

---

## 4. 자녀 초대코드 등록

<img src="./docs/gif/자녀초대코드등록.gif" width="80%" />

---

## 5. 검사 사전 동의

<img src="./docs/gif/검사사전동의.gif" width="80%" />

---

## 6. 동작 모방

<img src="./docs/gif/동작모방.gif" width="80%" />

---

## 7. 발화 모방

<img src="./docs/gif/발화모방.gif" width="80%" />

---

## 8. 대면 호명

<img src="./docs/gif/대면호명.gif" width="80%" />

---

## 9. 비대면 호명

<img src="./docs/gif/비대면호명.gif" width="80%" />

---

## 10. 검사 영상 조회

<img src="./docs/gif/검사영상조회.gif" width="80%" />

---

## 11. 검사 제출

<img src="./docs/gif/검사제출.gif" width="80%" />

---

## 12. 의사 환자 조회

<img src="./docs/gif/의사환자조회.gif" width="80%" />

---

## 13. 의사 차트 확인

<img src="./docs/gif/의사 차트 확인.gif" width="80%" />

---

## 14. 타임스탬프 선택

<img src="./docs/gif/타임스탬프 선택.gif" width="80%" />

---

## 15. 진단 결과 추가

<img src="./docs/gif/진료추가.gif" width="80%" />

---

## 16. 접수처 로그인

<img src="./docs/gif/접수처로그인.gif" width="80%" />

---

## 17. 접수처 초대코드 발급

<img src="./docs/gif/초대코드발급.gif" width="80%" />

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
