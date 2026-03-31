<div align="center">

# AITIME — Backend

### Spring Boot 기반 AI 자폐 진단 보조 시스템 서버

![SpringBoot](https://img.shields.io/badge/Spring_Boot-3.x-6DB33F?logo=springboot&logoColor=white)
![Java](https://img.shields.io/badge/Java-17-007396?logo=openjdk&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.x-DC382D?logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.x-FF6600?logo=rabbitmq&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3--compatible-C72E49?logo=minio&logoColor=white)

</div>

---

## 목차

1. [프로젝트 구조](#프로젝트-구조)
2. [기술 스택](#기술-스택)
3. [아키텍처](#아키텍처)
4. [도메인 설계](#도메인-설계)
5. [API 명세](#api-명세)
6. [인프라 연동](#인프라-연동)
7. [보안](#보안)
8. [환경 설정](#환경-설정)

---

## 프로젝트 구조

```
src/main/java/com/ssafy/aitime/
├── AiTimeBeApplication.java
│
├── application/                        # Application Service Layer
│   └── invitecode/
│       └── InviteCodeApplicationService.java
│
├── common/                             # 공통 모듈
│   ├── config/
│   ├── entity/                         # AuditableEntity, SoftDeletableEntity
│   ├── enums/
│   ├── exception/
│   └── response/
│       └── ApiResponse.java            # 공통 응답 래퍼
│
├── domain/                             # 핵심 비즈니스 도메인
│   ├── auth/                           # 전화번호 인증
│   ├── child/                          # 아동(환자) 관리
│   ├── exam/                           # 검사 및 영상 관리, AI 분석
│   ├── hospital/                       # 병원·의료진·예약 관리
│   ├── invite/                         # 초대 코드
│   ├── screening/                      # 실시간 스크리닝 세션 (LiveKit)
│   └── user/                           # 보호자 회원 관리
│
├── infra/                              # 외부 인프라 연동
│   ├── livekit/                        # LiveKit WebRTC
│   ├── minio/                          # MinIO (S3 호환 스토리지)
│   ├── rabbitmq/                       # RabbitMQ 메시지 큐
│   ├── redis/                          # Redis 설정
│   ├── sms/                            # CoolSMS 문자 인증
│   ├── swagger/                        # Swagger UI 설정
│   └── webclient/                      # AI 서버 WebClient
│
└── security/                           # Spring Security / JWT
    ├── config/
    ├── filter/
    ├── handler/
    ├── principal/                      # UserPrincipal, HospitalStaffPrincipal
    ├── provider/
    ├── repository/                     # Redis 기반 RefreshToken
    └── service/
```

---

## 기술 스택

| 분류 | 기술 | 비고 |
|------|------|------|
| Framework | Spring Boot 3.x | |
| Language | Java 17 | |
| ORM | Spring Data JPA | |
| Security | Spring Security + JWT | Access Token + HttpOnly Cookie(Refresh) |
| Database | MySQL 8.0 | |
| Cache / Session | Redis | Refresh Token, 스크리닝 세션 |
| Message Broker | RabbitMQ | AI 분석 요청/응답 |
| Object Storage | MinIO (S3 호환) | 영상 파일 저장, Presigned URL |
| Real-time | LiveKit | WebRTC 스크리닝 세션 |
| SMS | CoolSMS | 전화번호 인증 |
| API Docs | SpringDoc / Swagger UI | |
| Build | Gradle | |

---

## 아키텍처

<img src="../../docs/architecture.png" width="80%" />


### AI 분석 플로우

```
1. 보호자가 영상 4개를 MinIO에 직접 업로드 (Presigned PUT URL)
2. 업로드 완료 통지 → Spring Boot가 S3 존재 여부 HEAD 검증
3. 분석 요청 API 호출 → RabbitMQ 4개 큐에 각 태스크 메시지 publish
4. AI 서버가 큐 consume → 분석 수행
5. AI 서버가 결과를 analysis.resp 큐에 publish
6. Spring Boot AnalysisResultConsumer가 결과 consume → DB 저장 (ADOS 점수 산출)
```

---

## 도메인 설계

### 사용자 역할

| 역할 | 설명 | 인증 방식 |
|------|------|-----------|
| `USER` | 보호자 (아동 법정대리인) | JWT (UserPrincipal) |
| `HOSPITAL_STAFF` | 의사·간호사 등 의료진 | JWT (HospitalStaffPrincipal) |

### 핵심 도메인 및 엔티티

**child** — 아동(환아) 정보. 보호자(User)와 병원(Hospital) 양쪽에 연결됨

**exam** — 1회 검사 세션. 4가지 VideoType 영상과 ADOS 결과를 포함

| VideoType | 설명 |
|-----------|------|
| `NAME_FACING` | 대면 호명 반응 |
| `NAME_NON_FACING` | 비대면 호명 반응 |
| `POSE_IMITATION` | 동작 모방 |
| `SPEECH_IMITATION` | 발화 모방 |

**screening** — LiveKit 기반 실시간 WebRTC 스크리닝 세션. 상태는 Redis에 저장

**invite** — 병원이 보호자에게 발급하는 초대 코드. 아동-병원 연결에 사용

**ados** — 4개 영역의 ADOS 점수 및 세부 이벤트/트라이얼 결과 저장

### 공통 엔티티 구조

```
AuditableEntity          → createdAt, updatedAt
 └── BaseEntity          → id (UUID)
      └── SoftDeletable  → deletedAt (논리 삭제)
```

---

## API 명세

> Base URL: `/api/v1`  
> 전체 API는 Swagger UI(`/swagger-ui.html`)에서 확인 가능

### 보호자 (USER)

#### 인증 · 회원

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/user/login` | 로그인 (Access Token 반환, Refresh Token → HttpOnly Cookie) | ✗ |
| POST | `/user/refresh` | 토큰 갱신 | Cookie |
| POST | `/user/logout` | 로그아웃 | ✓ |
| GET | `/user/duplicate-id` | 아이디 중복 확인 | ✗ |
| POST | `/user/join` | 회원가입 | ✗ |
| GET | `/user/get-id` | 아이디 찾기 (전화번호) | ✗ |
| GET | `/user/verify-identity` | 본인 확인 | ✗ |
| PATCH | `/user/password` | 비밀번호 재설정 | ✗ |
| GET | `/user/me` | 내 정보 조회 | ✓ |
| PATCH | `/user/me` | 내 정보 수정 | ✓ |
| DELETE | `/user` | 회원 탈퇴 | ✓ |

#### 전화번호 인증

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/auth/phone/send` | 인증번호 발송 |
| POST | `/auth/phone/verify` | 인증번호 확인 |

#### 아동 관리

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/child` | 아동 등록 | ✓ |
| GET | `/child` | 아동 목록 조회 | ✓ |
| GET | `/child/{childId}` | 아동 홈 정보 조회 | ✓ |
| DELETE | `/child/{childId}` | 아동 삭제 | ✓ |
| POST | `/child/{childId}/hospital-link` | 초대 코드로 병원 연결 | ✓ |
| GET | `/child/{childId}/hospital-list` | 연결된 병원 목록 | ✓ |
| POST | `/child/{childId}/exam/start` | 검사 시작 | ✓ |

#### 검사 · 영상

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/exam/{childId}/examInfo` | 검사 진행도 조회 (4개 태스크 업로드 여부) | ✓ |
| POST | `/exam/{examId}/videos/presign-upload` | 영상 업로드 Presigned PUT URL 발급 | ✓ |
| POST | `/exam/{examId}/videos/{videoId}` | 영상 업로드 완료 통지 (S3 존재 검증) | ✓ |
| GET | `/exam/{examId}/videos/{videoId}` | 영상 재생 Presigned GET URL 발급 | ✓ |
| GET | `/exam/{examId}/videos/{videoId}/with-timestamps` | 영상 URL + 이벤트 타임스탬프 | ✓ |
| DELETE | `/exam/{examId}/videos/{videoId}` | 영상 삭제 | ✓ |
| POST | `/exams-analysis/{examId}/analyze` | 검사 전체 AI 분석 요청 | ✓ |
| POST | `/exams-analysis/videos/{videoId}/analyze` | 특정 영상 단독 재분석 | ✓ |

#### 스크리닝 (LiveKit)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/screening/start` | 스크리닝 세션 시작 (LiveKit 토큰 발급) | ✓ |
| GET | `/screening/status` | 현재 스크리닝 상태 조회 | ✓ |
| POST | `/screening/complete` | 스크리닝 완료 수신 (AI 서버 → Spring Boot) | 내부 |

---

### 의료진 (HOSPITAL_STAFF)

#### 로그인

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/hospital-staff/login` | 의료진 로그인 |
| POST | `/hospital-staff/refresh` | 토큰 갱신 |
| POST | `/hospital-staff/logout` | 로그아웃 |
| GET | `/hospital-staff/doctors` | 소속 병원 의사 목록 |

#### 예약 · 환자

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/doctor/patients` | 환자 목록 조회/검색 |
| GET | `/doctor/reservations/calendar` | 월별 예약 캘린더 조회 |
| GET | `/doctor/{hospitalChildrenId}/exams` | 환아별 검사 목록 조회 |
| GET | `/doctor/{hospitalChildrenId}/ados-report` | ADOS 시계열 그래프 데이터 |
| GET | `/doctor/{hospitalChildrenId}/initial-report` | 환아 초기 리포트 |
| GET | `/doctor/reservations` | 예약 목록 조회 |

#### 초대 코드

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/invite-code` | 초대 코드 발급 |
| DELETE | `/invite-code/{inviteCodeId}` | 초대 코드 삭제 |
| GET | `/invite-code/{inviteCodeId}/status` | 초대 코드 상태 조회 |
| GET | `/invite-code/patients` | 초대 코드 연결 환자 목록 |

---

### 공통 응답 형식

```json
{
  "status": 200,
  "message": "요청이 처리되었습니다.",
  "data": { ... }
}
```

---

## 인프라 연동

### Redis

- **Refresh Token 저장**: `refreshToken:{userId}` 키로 저장, TTL = 14일
- **스크리닝 세션 관리**: LiveKit 방 정보 및 세션 상태 저장, TTL = 1시간

### RabbitMQ

AI 분석 파이프라인을 위한 5개 큐:

| 큐 이름 | 방향 | 설명 |
|---------|------|------|
| `analysis.req.task1` | → AI | 대면 호명 반응 분석 요청 |
| `analysis.req.task2` | → AI | 비대면 호명 반응 분석 요청 |
| `analysis.req.task3` | → AI | 동작 모방 분석 요청 |
| `analysis.req.task4` | → AI | 발화 모방 분석 요청 |
| `analysis.resp` | ← AI | 분석 결과 수신 |

`AnalysisPublisher`가 요청 메시지를 publish하고, `AnalysisResultConsumer`가 결과를 consume하여 ADOS 점수를 DB에 저장합니다.

### MinIO (Object Storage)

- S3 호환 스토리지로 영상 파일 관리
- 클라이언트가 **Presigned PUT URL**을 통해 서버를 거치지 않고 MinIO에 직접 업로드
- 업로드 완료 후 Spring Boot가 **HEAD 요청**으로 실제 파일 존재 여부 검증
- 파일 조회 시 **Presigned GET URL** 발급 (만료 시간 1~3600초 설정 가능)
- 최대 파일 크기: 500MB

### LiveKit

- WebRTC 기반 실시간 스크리닝 세션
- 보호자가 `/screening/start` 호출 시 LiveKit 토큰 발급
- 세션 완료 시 AI 서버가 `/screening/complete`로 콜백

### CoolSMS

- 회원가입 및 본인 인증 시 전화번호 기반 SMS 인증번호 발송

---

## 보안

### JWT 토큰 전략

```
Access Token
├── 만료: 15분 (900,000ms)
├── 전달: Authorization: Bearer {token}
└── 저장: 클라이언트 메모리

Refresh Token
├── 만료: 14일 (1,209,600,000ms)
├── 전달: HttpOnly Cookie
└── 저장: Redis
```

### 이중 인증 Principal

보호자와 의료진의 권한 체계를 별도 Principal로 분리하여 관리합니다.

```java
UserPrincipal           // 보호자 (USER)
HospitalStaffPrincipal  // 의료진 (HOSPITAL_STAFF)
```

### 주요 보안 설정

- CORS 설정: Nginx를 통한 프록시 환경 고려
- CSRF: Stateless API이므로 비활성화
- 쿠키: HttpOnly + Secure + SameSite 설정

---

## 환경 설정

### 애플리케이션 프로파일

| 프로파일 | 설명 |
|----------|------|
| `dev` | 개발 환경 (기본값) |
| `prod` | 운영 환경 |
| `test` | 테스트 환경 |

### 주요 환경 변수

```yaml
# LiveKit
LIVEKIT_URL: ws://localhost:7880
LIVEKIT_API_KEY: {api-key}
LIVEKIT_API_SECRET: {api-secret}

# AI Server
AI_SERVER_URL: http://localhost:8000

# MinIO / S3
minio.endpoint: {endpoint}
minio.access-key: {access-key}
minio.secret-key: {secret-key}
minio.bucket-name: aitime

# MySQL
spring.datasource.url: jdbc:mysql://{host}:3306/aitime
spring.datasource.username: {username}
spring.datasource.password: {password}

# Redis
spring.data.redis.host: {host}
spring.data.redis.port: 6379

# RabbitMQ
spring.rabbitmq.host: {host}
spring.rabbitmq.username: {username}
spring.rabbitmq.password: {password}
```

### 실행 방법

Backend는 Docker Compose를 통해 실행합니다. 아래 설정 파일(`docker-compose.spring.yml`)을 사용하여 Spring 컨테이너를 단독으로 기동할 수 있습니다.

```yaml
services:
  spring:
    build:
      context: ../BE/ai_time_be
      dockerfile: ../../docker/dockerfiles/Dockerfile.backend
    container_name: spring
    ports:
      - "127.0.0.1:8081:8080"
    env_file:
      - .env
    environment:
      DB_HOST: mysql
      REDIS_HOST: redis
      RABBITMQ_HOST: rabbitmq
      MINIO_ENDPOINT: ${MINIO_ENDPOINT}
      LIVEKIT_URL: http://livekit:7880
      AI_SERVER_URL: http://screening:8000
      TZ: ${TZ:-Asia/Seoul}
      JAVA_OPTS: -Xms512m -Xmx768m -XX:MaxMetaspaceSize=256m -XX:+UseG1GC -XX:MaxGCPauseMillis=200
    networks:
      - cmn-network
    restart: unless-stopped
    mem_limit: 1g
    mem_reservation: 700m
    memswap_limit: 1g

networks:
  cmn-network:
    external: true
    name: cmn-network
```

**실행 순서:**

1. `.env` 파일에 환경 변수를 설정합니다 (주요 환경 변수 섹션 참조).
2. 공유 Docker 네트워크가 없을 경우 먼저 생성합니다.
   ```bash
   docker network create cmn-network
   ```
3. Docker Compose로 Spring 컨테이너를 빌드 및 실행합니다.
   ```bash
   docker compose -f docker-compose.spring.yml up -d --build
   ```
4. 컨테이너 로그를 확인하여 정상 기동 여부를 검증합니다.
   ```bash
   docker logs -f spring
   ```

> **참고:** Spring 컨테이너는 MySQL, Redis, RabbitMQ가 동일한 `cmn-network`에서 먼저 실행 중이어야 정상적으로 연결됩니다.

서버 기동 후 API 문서: `http://localhost:8080/api/v1/swagger-ui.html`
