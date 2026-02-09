# 포팅 매뉴얼 (Porting Manual)

본 문서는 본 프로젝트를 새로운 서버 환경에 배포하기 위한 포팅 매뉴얼이다.  
Docker 기반 환경을 기준으로 작성되었으며, Ubuntu 22.04 LTS 환경에서 검증되었다.

---

## 0. 아키텍처 개요

### 0-1. 전체 구조 설명

외부 사용자의 요청은 Nginx를 통해 내부 서비스로 프록시된다.

#### 아키텍처 다이어그램

[📊 인터랙티브 아키텍처 보기](./aitime-architecture.html)

### 0-2. 주요 구성 요소

- **Nginx**: Reverse Proxy 및 SSL 종료
- **Spring Boot**: 비즈니스 로직 처리
- **React**: 사용자 웹 UI
- **LiveKit**: WebRTC 기반 실시간 검사
- **MinIO**: 영상 파일 저장 (S3 호환)
- **RabbitMQ**: 비동기 메시징
- **MySQL / Redis**: 데이터 저장 및 캐시

---

## 1. 서버 요구사항 & 사전 설치

### 1-1. EC2 서버 사양

- Instance Type: `r5.xlarge`
- OS: `Ubuntu 22.04 LTS`
- Storage: `100GB gp3`

### 1-2. 필수 패키지

- Docker / Docker Compose
- Nginx
- UFW (방화벽)

---

## 2. 네트워크 / 방화벽 설정

### 2-1. UFW 인바운드 포트

| 포트 | 프로토콜 | 용도 |
|------|---------|------|
| 22 | TCP | SSH |
| 80 | TCP | HTTP |
| 443 | TCP | HTTPS |
| 8099 | TCP | RabbitMQ Management |
| 8020 | TCP | LiveKit TURN |
| 41000 | UDP | LiveKit TURN |
| 50000-51000 | UDP | WebRTC Media |

### 2-2. UFW 설정 명령어

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing

sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8099/tcp
sudo ufw allow 8020/tcp
sudo ufw allow 41000/udp
sudo ufw allow 50000:51000/udp

sudo ufw --force enable
sudo ufw status verbose
```

### 2-3. AWS 보안그룹

- UFW와 동일한 포트를 반드시 AWS 보안그룹에도 개방해야 함
- 둘 중 하나라도 막혀 있으면 서비스 접근 불가

---

## 3. Nginx 설정

### 3-1. 역할

- 경로 기반 Reverse Proxy
- WebSocket(/rtc) 지원
- MinIO Presigned URL CORS 처리
- HTTPS 적용 (Certbot)

### 3-2. 설정 파일 위치

```bash
/etc/nginx/sites-available/default
```

### 3-3. 주요 설정 내용

#### WebSocket 지원 맵

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
```

#### 서버 블록

```nginx
server {
    server_name i14a501.p.ssafy.io;  # 본인 도메인으로 변경
    
    # ... location 블록들 ...
    
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/i14a501.p.ssafy.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/i14a501.p.ssafy.io/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
```

#### Location 블록 상세

| 경로 | 프록시 대상 | 포트 | 비고 |
|------|------------|------|------|
| `/api/` | Spring Boot Backend | 8081 | REST API |
| `/jenkins/` | Jenkins CI/CD | 8088 | 빌드 파이프라인 |
| `/aitime/exams/` | MinIO S3 | 9000 | CORS 설정 포함 |
| `/rtc` | LiveKit | 7880 | WebSocket 지원 |
| `/rabbitmq/` | RabbitMQ Management | 15672 | WebSocket 지원 |
| `/` | React Frontend | 3000 | SPA 기본 라우팅 |

#### MinIO CORS 설정 (중요)

```nginx
location /aitime/exams/ {
    client_max_body_size 0;
    
    # CORS 헤더 - Presigned URL 지원
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, HEAD, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT, User-Agent, X-Requested-With, If-Modified-Since, Cache-Control, Content-Type, Range, Authorization, X-Amz-Date, X-Amz-Content-Sha256, X-Amz-User-Agent, X-Amz-Security-Token' always;
    
    # OPTIONS preflight 처리
    if ($request_method = OPTIONS) {
        return 204;
    }
    
    # MinIO 응답 헤더 숨기기 방지
    proxy_hide_header Access-Control-Allow-Origin;
    
    # Host 헤더 유지 (서명 검증용)
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    proxy_pass http://127.0.0.1:9000;
}
```

#### LiveKit WebSocket 설정

```nginx
location ^~ /rtc {
    proxy_pass http://127.0.0.1:7880;
    
    # WebSocket 업그레이드
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    
    # 긴 타임아웃 (실시간 검사용)
    proxy_send_timeout 3600s;
    proxy_read_timeout 3600s;
}
```

### 3-4. SSL 인증서 발급 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# 인증서 발급
sudo certbot --nginx -d i14a501.p.ssafy.io

# 자동 갱신 확인
sudo certbot renew --dry-run
```

### 3-5. HTTP → HTTPS 리다이렉트

```nginx
server {
    listen 80;
    server_name i14a501.p.ssafy.io;
    return 301 https://$host$request_uri;
}
```

### 3-6. 설정 적용

```bash
# 설정 파일 문법 체크
sudo nginx -t

# Nginx 재시작
sudo systemctl reload nginx

# Nginx 상태 확인
sudo systemctl status nginx
```

### 3-7. 문제 해결

```bash
# 에러 로그 확인
sudo tail -f /var/log/nginx/error.log

# 액세스 로그 확인
sudo tail -f /var/log/nginx/access.log
```

---

## 4. 소스 받기 & 디렉터리 구조

```bash
cd /home/ubuntu/src
git clone https://lab.ssafy.com/s14-webmobile1-sub1/S14P11A501.git
cd S14P11A501
```

### 디렉터리 개요

- `/docker`: docker-compose 파일
- `/BE`: Spring Backend
- `/FE`: React Frontend
- `/AI`: AI 서비스

---

## 5. Docker 공통 리소스 준비

### 5-1. Docker Network 생성

```bash
docker network create cmn-network || true
```

### 5-2. Docker Volume 생성

```bash
docker volume create mysql_data || true
docker volume create redis_data || true
docker volume create jenkins_home || true
```

---

## 6. 환경변수(.env) / 시크릿 파일

### 6-1. .env 생성

```bash
cd docker
cp .env.example .env
```

### 6-2. 반드시 수정해야 하는 항목

- MySQL 비밀번호
- JWT_SECRET (32자 이상)
- MinIO 비밀번호
- CoolSMS API Key / Secret
- LiveKit API Key / Secret
- 서비스 도메인

### 6-3. Spring Boot 설정 파일

백엔드 소스코드의 설정 파일도 환경에 맞게 수정해야 합니다.

**파일 위치:**
```
BE/ai_time_be/src/main/resources/
├── application.yml           # 공통 설정
└── application-prod.yml      # 프로덕션 환경 설정
```

exec 폴더에 있는 파일 해당 위치로 복사해야 합니다.

---

## 7. Docker Compose 기동 순서

### ⚠️ 순서 중요

1. 공통 인프라
2. DB / Redis / RabbitMQ
3. Backend
4. AI 서버 (하나씩 빌드 권장)
5. LiveKit
6. Frontend

## 7-1. Makefile 사용 (권장)

```bash
cd /home/ubuntu/src/S14P11A501/docker

# 1. 초기 설정
make init

# 2. 공통 인프라 (MinIO 등)
make cmn start

# 3. Backend
make be start

# 4. AI 서버 (순차적으로)
make ai1 start
make ai2 start
make ai3 start
make ai4 start

# 5. LiveKit
make livekit start

# 6. Frontend
make fe start

# 로그 확인
make be dlog
make ai1 dlog

# 서비스 중지
make fe down
make be down
```

### 7-2. docker-compose 직접 사용

```bash
docker compose -f docker-compose.cmn.yml up -d
docker compose -f docker-compose.db.yml up -d
docker compose -f docker-compose.backend.yml up -d --build
docker compose -f docker-compose.ai1.yml up -d --build
docker compose -f docker-compose.ai2.yml up -d --build
docker compose -f docker-compose.livekit.yml up -d
docker compose -f docker-compose.frontend.yml up -d --build
```

### 7-3. Makefile 명령어 정리

| 명령어 | 설명 |
|--------|------|
| `make init` | 네트워크 + 볼륨 생성 |
| `make <svc> start` | 빌드 후 시작 (up -d --build) |
| `make <svc> up` | 빌드 없이 시작 (up -d) |
| `make <svc> down` | 중지 및 제거 |
| `make <svc> dlog` | 로그 실시간 확인 |

**서비스 목록**: `cmn` `fe` `be` `ai1` `ai2` `ai3` `ai4` `livekit` `screening`

---

## 8. 초기 데이터 / DB Dump 적용

### 8-1. MySQL 데이터 적용

```bash
docker exec -i mysql \
  mysql -u root -p aitime < aitime.sql
```

---

## 9. 시연 시나리오

### 9-1. 부모 페이지 - 회원가입 및 자식 등록

#### 1) 회원가입

1. 부모 회원가입 페이지 접속
2. 기본 정보 입력
   - 아이디 (중복 확인 필수)
   - 비밀번호
   - 휴대폰 번호 (SMS 인증 필수)
   - 기타 개인정보
3. 회원가입 완료

#### 2) 로그인

1. 회원가입한 계정으로 로그인

#### 3) 자식 추가

1. 자식 추가 메뉴 선택
2. 아이 정보 입력
   - 이름
   - 나이
   - 성별
3. 검사 대상 아이 등록 완료

---

### 9-2. 접수처 페이지 - 초대코드 발급

#### 1) 접수처 로그인

- URL: `/reception/login` (또는 접수처 전용 페이지)
- ID: `desk1`
- PW: `password123!`

#### 2) 초대코드 발급

1. "초대코드 발급" 버튼 클릭
2. 환아 정보 입력
   - 환자 이름
   - 생년월일
   - 보호자 연락처 (회원가입 시 등록한 번호)
   - 담당의사 선택
   - 예약 일시
3. 초대코드 생성 확인

#### 3) 초대코드 복사

- 발급된 초대코드를 복사하여 보호자에게 전달

---

### 9-3. 부모 페이지 - 초대코드 등록 및 검사 진행

#### 1) 초대코드 등록

1. 아이 페이지에서 "초대코드 입력" 메뉴 선택
2. 접수처에서 받은 초대코드 입력
3. 병원 연동 활성화 확인
4. AI 검사 기능 활성화

#### 2) 검사 페이지 접근

1. 검사 페이지 진입
2. 유의사항 숙지
3. 4개 검사 미션 확인

---

### 9-4. 검사 수행

#### 1) 검사 선택

- 진행할 검사 선택 (총 4개 중 1개)

#### 2) 사전 준비

1. 사전 안내 영상 시청
2. 환경 검사 (스크리닝) 진행
   - 조명 확인
   - 카메라 위치 확인
   - 배경 확인
3. 환경이 적절하면 "검사 시작" 버튼 활성화

#### 3) 검사 진행

1. "검사 시작" 버튼 클릭
2. 화면의 가이드에 따라 미션 수행
3. 검사 영상 자동 녹화 및 업로드

#### 4) 검사 완료

1. 4개 검사 모두 완료
2. "리포트 전송하기" 버튼 활성화
3. 리포트 전송 → AI 분석 시작

---

### 9-5. 의사 페이지 - 검사 결과 확인

#### 1) 의사 로그인

- URL: `/doctor/login` (또는 의사 전용 페이지)
- ID: `의사{숫자}` (예: `의사1`, `의사2`)
  - 숫자는 초대코드 발급 시 선택한 의사 번호
- PW: `password123!`

#### 2) 예약 환아 확인

1. 캘린더에서 날짜별 예약 환아 리스트 확인
2. 검사 완료된 환아 식별 (완료 표시)

#### 3) AI 검사 결과 확인

환아 선택 시 다음 정보 확인 가능:

1. **검사 영상**
   - 4개 미션별 녹화 영상
   - 영상 재생 및 다운로드

2. **타임스탬프**
   - 주요 행동 발생 시점 표시
   - 확인 필요 구간 하이라이트

3. **ADOS 점수**
   - AI가 분석한 ADOS 검사 점수
   - 항목별 세부 점수
   - 종합 소견

4. **행동 분석 결과**
   - 포즈 추정 결과
   - 음성 모방 정확도
   - 이름 반응성
   - 기타 관찰 사항

---

### 9-6. 시연 플로우 요약

```
1. [부모] 회원가입 → 로그인 → 자식 추가
   ↓
2. [접수처] 로그인 → 초대코드 발급 → 코드 전달
   ↓
3. [부모] 초대코드 등록 → 검사 페이지 접근
   ↓
4. [검사] 안내 영상 시청 → 환경 검사 → 4개 미션 수행 → 리포트 전송
   ↓
5. [의사] 로그인 → 예약 환아 확인 → AI 검사 결과 분석
```

---

## ✅ 포팅 완료 체크리스트

- [ ] .env 설정 완료
- [ ] 방화벽 / 보안그룹 확인
- [ ] Nginx 정상 동작
- [ ] DB 초기 데이터 적용
- [ ] LiveKit 연결 확인
- [ ] 시연 시나리오 정상 동작