<aside>

✅ 작성자 : 박동한

✅ 작성일 : 26.01.17

</aside>

<aside>

본 문서는 프론트 배포를 알아보고 그 과정에서의 네트워크와 보안을 함께 다루며,

Vercel, Netlify, Nginx를 비교한다.

</aside>

<aside>

</aside>

프론트 배포는 “빌드해서 나온 정적 파일을, 사용자에게 빠르고 안전하게 전달”하는 일

---

## 1) 한 줄로 감 잡기

- **Vercel / Netlify**: 정적 호스팅 + CDN + HTTPS + 배포 자동화를 **플랫폼**이 해주는 방식 (PaaS 느낌)
- **Nginx**: 내가 가진 서버/VM/컨테이너에 직접 올려서 **내가** 운영하는 방식 (IaaS/자체 운영)

---

## 2) 프론트 배포 원리: 빌드 → 서빙 → 캐시/CDN

### (1) 빌드

- `npm run build`
    
    → `dist/` 또는 `build/` 폴더에 정적 파일 생성
    
    (보통 `index.html` + JS 번들 + CSS + 이미지 등)
    

### (2) 서빙

- 사용자가 `https://주소주소.com` 접속
- 서버/CDN이 `index.html` 내려줌
- 브라우저가 `index.html` 안의 JS/CSS를 추가로 받아 실행 → 화면 렌더링

### (3) 캐시/CDN

- JS/CSS/이미지 같은 정적 파일은 **CDN + 장기 캐시**와 궁합이 좋음
- `index.html`은 자주 바뀌어서 캐시 전략을 다르게 둠

여기까지는 똑같고, **2)~3)과 HTTPS/라우팅/배포 자동화를 누가 맡느냐**가 Vercel, Netlify, Nginx의 핵심 차이다.

---

## 3) 빌드 결과물을 이해하는 핵심 용어들

### 번들(Bundle)

여러 JS/CSS 파일을 **한(또는 몇) 개로 묶은 결과물**.

- 배포 시에는 요청 수를 줄이고 최적화를 위해 **압축(minify)/난독화 효과/트리 쉐이킹**이 함께 들어가는 경우가 많음
- 요즘은 **코드 스플리팅**(라우트/컴포넌트 단위로 쪼개서 필요한 순간 로드)도 있어서 여러 chunk로 쪼개어 최적화
- 예: `app.3f2a9.js`, `vendor.a81c0.js`

### 트리 쉐이킹(Tree-shaking)

“import는 했지만 실제로 안 쓰는 코드”를 **번들에서 제거**하는 최적화.

- 보통 **ESM(import/export, ECMAScript Modules)** 구조에서 잘 동작
    - 단, 패키지의 sideEffects 설정, 부작용(side effect) 있는 코드가 섞이면 제거가 제한
- 예: lodash 전체를 가져왔지만 함수 1개만 쓰면 나머지 제거

### 난독화(Obfuscation)

JS 코드를 사람이 읽기 어렵게 바꾸는 것.

- 변수명 축약, 구조 변형 등
- 보안의 핵심은 아니고, **프로덕션 빌드(minify)의 부수 효과**로 따라온다
- 별도의 도구가 될 수도 있으나 minify/uglify에 가까운 수준

### CDN(Content Delivery Network)

전 세계 여러 지역에 파일을 복제해 두고 **사용자와 가까운 서버에서 빠르게 내려주는 네트워크**.

- 장점: 빠름, 트래픽 분산, 원본 서버 부담 감소
- 프론트의 JS/CSS/이미지 같은 **정적 파일**은 대부분 CDN으로 나감

---

## 4) “CDN”과 “CDN 엣지(Edge)”는 뭐가 다른가?

- **CDN**: 파일을 캐시해 **가까운 곳에서 전달**하는 네트워크(정적 파일 전달 중심)
- **CDN 엣지(Edge)**: 그 **엣지 노드에서 코드까지 실행**하는 것(Edge Runtime/Edge Functions)

### 엣지에서 코드를 실행하는 이유

1. **지연시간 감소**: 중앙 서버 왕복 없이 가까운 곳에서 처리(리다이렉트/인증 체크 등)
2. **원본 서버 보호**: 입구에서 필터링(봇 차단, [rate limit](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21), 간단 [WAF](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21))
    
    기술은 환경에 따라 합쳐지거나 분리되기도 함
    
3. **개인화/실험**: A/B 테스트, 국가/언어 분기 등을 “처음 응답부터” 처리
    
    A/B 테스트 : 사용자를 무작위로 A그룹/B그룹으로 나눠 **서로 다른 UI/기능/문구**를 보여주고 성과를 비교하는 실험
    
4. **캐시 효율 개선**: 사용자 그룹별로 캐시 키를 다르게 구성 가능
- 단, Edge에서 실행되는 코드는 제약(런타임 제한/콜드스타트/지역별 상태 공유 어려움)이 있을 수 있음

---

## 5) SPA/SSR/SSG/ISR: “어떤 HTML을 언제 만들까?”의 차이

**렌더링 방식**에 따라 “서버(또는 엣지)가 개입하는 시점”이 달라진다.

### SPA (Single Page Application - Client Side Randering)

처음 `index.html` 하나 받고 이후 화면 전환은 **JS 라우팅**으로 처리.

- 장점: 앱처럼 부드러움
- 단점: SSR 없으면 초기 로딩/SEO가 불리할 수 있음

### SSR (Server-Side Rendering)

페이지 HTML을 **서버가 먼저 만들어서** 브라우저에 줌.

- 장점: 초기 화면 빠름, SEO 유리
- 단점: 서버 비용/복잡도 증가

### SPA도 SSR 해야 하는가?

반드시 그럴 필요는 없음.

- SSR/SSG가 유리한 경우
    - 검색 노출(SEO)이 중요(콘텐츠/마케팅 페이지)
    - 초기 화면 체감이 중요
    - 링크 공유 시 메타/미리보기(OG) 중요
- SPA로 충분한 경우
    - 로그인 이후 대시보드/어드민/내부 서비스
    - SEO가 거의 필요 없음
    - 개발/운영 단순성이 더 중요

### 하이드레이션(Hydration)

SSR로 내려온 “이미 그려진 HTML”에 브라우저가 JS를 붙여 **상호작용 가능하게 만드는 과정**.

SSR 직후에는 화면은 보이지만 버튼 클릭 같은 이벤트가 “죽어있을” 수 있고, 하이드레이션이 끝나야 SPA처럼 동작한다.

### SEO (Search Engine Optimization)

검색 엔진이 페이지를 잘 이해하고 노출하도록 하는 것.

- 핵심: **초기 HTML에 콘텐츠가 있으면 유리**(SSR/SSG가 강한 이유)
- 메타태그, 구조화 데이터, 페이지 속도, 접근성 등도 중요
- SPA는 JS 실행 전 HTML이 비어 있을 수 있어 SEO가 불리할 수 있음(검색엔진마다 JS 렌더링 지원 수준 차이)

### SSG (Static Site Generation)

**빌드 시점에 HTML을 미리 만들어** 배포.

- 장점: 빠름, 서버 비용 낮음, CDN/캐시와 궁합 좋음, SEO 좋음
- 단점: 데이터가 자주 바뀌면 재빌드/재배포가 필요

### ISR (Incremental Static Regeneration)

SSG를 기본으로 하되, 필요할 때 **일부 페이지만 다시 생성해 갱신**(Next.js에서 유명).

- “정적 + 주기적/조건부 재빌드” 느낌
- 빠름과 최신 사이 타협점
- 정적 페이지 재성성이기에 캐시/재검증(revalidate) 정책도 함께 고려되어야 함.

![image.png](attachment:7a039d90-ff4b-4c1c-bc99-ac9496d9cb5f:image.png)

---

## 6) Vercel vs Netlify vs Nginx: 무엇이 어떻게 다른가?

공통적으로 “정적 파일을 사용자에게 전달”하지만, 운영 주체와 기능 범위가 다르다.

### Vercel

**강점**

- Next.js와 궁합 최강(SSR/ISR/Edge)
- Git 연동 + PR마다 Preview Deployments가 매우 편함
- 전 세계 CDN 배포 + 서버리스/엣지 기능 연결이 쉬움

**원리**

- GitHub push → Vercel 빌드 → 결과물을 CDN(엣지)에 배포
- 도메인/HTTPS 자동
- 라우팅(특히 Next.js)은 플랫폼 규칙 기반으로 처리

**잘 맞는 경우**

- Next.js 사용
- 협업/미리보기 배포가 중요
- SSR/ISR/Edge를 쉽게 쓰고 싶을 때

---

### Netlify

**강점**

- React/Vite/Vue 같은 정적 사이트 운영 편의(폼/리다이렉트/헤더 설정 등)
- Git 연동 + Preview 배포 강함
- `_redirects`, `netlify.toml`로 SPA 라우팅/리다이렉트 규칙 설정이 쉬움

**원리**

- GitHub push → Netlify 빌드 → CDN 배포
- HTTPS/도메인/캐시/리다이렉트 규칙을 플랫폼이 처리

**잘 맞는 경우**

- 순수 SPA/정적 사이트 중심
- 리다이렉트/헤더 정책을 빠르게 만지고 싶을 때

---

### Nginx

**강점**

- 성능/보안 헤더/[프록시](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21)/인증/비용 등 **모든 걸 내가 통제**
- 백엔드/AI 서버와 같은 VM(EC2)에서 함께 운영 가능
- `/`는 정적 파일, `/api`는 백엔드로 프록시 같은 구성이 깔끔함

**원리**

- EC2(또는 컨테이너)에 `dist/` 업로드/배포
- Nginx가 정적 파일 직접 서빙
- 필요하면 `/api`를 Spring/FastAPI로 reverse proxy
- HTTPS도 보통 내가 설정(예: Let’s Encrypt)

**잘 맞는 경우**

- 인프라/운영을 직접 책임지는 팀
- 커스텀 요구가 많음(폐쇄망/사내망/정교한 보안 정책)
- 비용/성능을 내 손으로 최적화하고 싶을 때
- “Nginx 앞 + S3+CloudFront” 같은 조합도 가능

**참고**

- CDN이 없으므로 별도로 (CloudFront/Cloudflare 등) 붙임

| 항목 | Vercel / Netlify (플랫폼 운영) | Nginx (내가 운영) | 실무 메모 |
| --- | --- | --- | --- |
| **배포(Deploy)** | ✅ Git 연동 자동 배포, Preview 배포 | 🟨 CI 구성하면 자동화 가능 / 아니면 수동 | Nginx도 Jenkins/GHA로 자동화 가능(대신 내가 만듦) |
| **빌드 환경/캐시** | ✅ 플랫폼 빌드 + 캐시 제공 | 🟨 내가 빌드 서버/캐시 설계 | 대규모면 빌드 캐시가 비용/시간에 영향 큼 |
| **정적 파일 서빙** | ✅ CDN에 자동 배포 | ✅ Nginx로 고성능 서빙 | Nginx는 “원본(오리진)” 역할에 강함 |
| **CDN(전세계 캐시)** | ✅ 기본 포함 | ❌ 별도 구성 필요(CloudFront/Cloudflare 등) | 실무는 “CDN + Nginx 오리진” 조합이 흔함 |
| **HTTPS/TLS 인증서** | ✅ 자동 발급/갱신 | 🟨 Let’s Encrypt 등으로 직접 | TLS 종료를 CDN/LB에서 할 수도 있음 |
| **도메인/DNS 연결** | ✅ 가이드 쉬움 | ✅ 내가 직접 설정 | 루트 도메인(apex)은 CNAME 제약 때문에 DNS 기능(ALIAS/ANAME 등) 이슈 주의 |
| **SPA 새로고침 404 대응** | ✅ 리라이트/리다이렉트 쉽게 설정 | 🟨 Nginx 설정 직접 필요 | Nginx: `try_files ... /index.html` |
| **SSR/ISR 지원** | ✅ (특히 Vercel+Next.js 강함) | 🟨 직접 서버(Next 서버 등) 운영해야 함 | SSR은 “정적 호스팅”이 아니라 “런타임 서버”가 필요 |
| **엣지에서 코드 실행(Edge)** | ✅ Edge Functions/Serverless 제공 | 🟨 별도 플랫폼/프록시로 구현 | 엣지는 제약(런타임/상태 공유/콜드스타트) 고려 |
| **라우팅/프록시(/api)** | 🟨 가능(규칙/함수로 처리) | ✅ Nginx가 제일 깔끔 | `/` 정적, `/api` 프록시가 대표 패턴 |
| **보안 헤더(CSP/HSTS 등)** | 🟨 설정 가능(플랫폼 방식) | ✅ 내가 원하는 대로 | “내가 통제 vs 플랫폼 규칙”의 차이 |
| **WAF/봇 차단** | 🟨 플랜/연동에 따라 | 🟨 직접 구성(Cloudflare/AWS WAF 등) | 보통 CDN/WAF를 앞단에 둠 |
| **레이트리밋** | 🟨 일부 제공/함수로 구현 | ✅ Nginx/게이트웨이에서 중앙화 쉬움 | AI/API 폭주 방어는 입구에서 끊는 게 편함 |
| **로그/모니터링** | 🟨 플랫폼 로그 제공(한계/플랜 차이) | ✅ 내가 수집/보관/분석 | Nginx access/error log + APM/metrics |
| **장애 대응/온콜** | ✅ 플랫폼이 인프라 장애 대부분 처리 | ❌ 내가 다 책임 | “운영 인력/체계 있나?”가 선택의 핵심 |
| **비용 구조** | ✅ 간편(트래픽/빌드/함수 기반) | 🟨 서버 고정비 + CDN/도메인 추가 | 트래픽 폭증 시: 플랫폼 과금 vs 서버/대역폭 설계 |

---

## 7) 도메인, DNS, CNAME: 연결의 기본

- **도메인(domain)**: `example.com` 같은 사람이 읽는 주소
- **DNS**: 도메인을 실제 서버/CDN 엔드포인트로 연결하는 “인터넷 주소록”
    - 대표 레코드: **A(IPv4)**, **AAAA(IPv6)**, **CNAME(별명 연결)**
- **CNAME**: 도메인을 다른 도메인으로 연결(예: `www.myapp.com` → `myapp.vercel.app`)
    
    → IP가 바뀔 수 있는 플랫폼에 붙일 때 편함
    

---

## 8) HTTPS/TLS: “어디서 TLS를 끝내나(termination)”가 포인트

- **TLS**는 HTTPS의 암호화 표준
    
    (암호화/무결성/신원 확인)
    

### TLS 종료(termination)는 어디서 하나?

- **Vercel/Netlify**: 플랫폼/CDN이 TLS 종료(인증서 발급/갱신 자동)
- **Nginx**: Nginx가 TLS 종료하도록 직접 인증서 설정(예: Let’s Encrypt)

### Nginx에서 HTTPS 대표 패턴

1. Let’s Encrypt + certbot으로 인증서 발급/갱신 자동화
2. `listen 443 ssl;` + 인증서 경로 설정
3. 80 → 443 리다이렉트
4. certbot timer/cron + Nginx reload

---

## 9) 보안: WAF, ASN, XSS, CSP, Sanitize까지 한 번에

### WAF(Web Application Firewall)

웹 공격을 **입구에서 차단**하는 방화벽.

- SQLi/[XSS](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21) 패턴, 비정상 봇, 특정 국가/[ASN](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21)/대역 차단 등
- 위치: 보통 **CDN/엣지 앞단** 또는 [**게이트웨이](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21)(Nginx 앞/옆)**

### ASN(Autonomous System Number)

“이 IP 대역이 어느 조직(통신사/클라우드/기업) 소속인지”를 식별하는 번호.

- [WAF](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21) 정책에서 “특정 ASN(예: 봇이 많은 클라우드 ASN)을 제한” 같은 식으로 활용

### XSS(Cross-Site Scripting)

악성 JS가 끼어들어 사용자의 브라우저에서 실행되게 하는 공격.

- 세션/토큰 탈취, 피싱, 화면 변조 등
- 대표 원인: 사용자 입력을 **그대로 HTML로 출력**
- 방어 핵심:
    - 출력 시 **이스케이프/인코딩**
    - 위험한 `innerHTML` 사용 피하기(또는 [sanitize](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21))
    - [CSP](https://www.notion.so/2eb00db5cb9f80a6baeec1ee7cc01370?pvs=21) 적용
    - 쿠키는 `HttpOnly`, `Secure`, `SameSite` 고려
        - HttpOnly 쿠키는 CSRF 고려해야 함
    - localStorage에 토큰 저장은 피하기
    - 

### CSP(Content-Security-Policy)

브라우저에게 “어떤 스크립트/리소스만 로드, 실행 가능한지”를 알려주는 보안 헤더.

- XSS가 터져도 **실행 자체를 제한**
- 현실 팁: 처음부터 빡세게 하면 기능이 깨질 수 있어 **Report-Only로 시작 → 점진 강화**가 흔함
- 추가 보안 헤더 : `HSTS`, `X-Frame-Options`(또는 frame-ancestors), `Referrer-Policy`, `Permissions-Policy` (Nginx는 직접 넣어야 한다고 함)

### Sanitize(새니타이즈)

사용자 입력에 섞일 수 있는 위험한 HTML/JS를 **허용 목록 기반으로 정리/제거**.

- **Escape(이스케이프)**: 텍스트로만 보여줄 거면 이게 정석(가장 안전)
- **Sanitize(허용 목록)**: 일부 HTML(에디터/마크다운)을 허용해야 할 때
- 가능하면 서버에서도 한 번 더 검증하는 게 좋음(프론트만 믿지 않는 것)

---

## 10) 프록시, 게이트웨이, 레이트리밋: “입구를 하나로”

보안/정책을 **입구(엣지/게이트웨이)에 몰아넣는 게 운영 난이도를 낮춘다**

### 프록시 / 리버스 프록시

클라이언트 요청을 대신 받아서 다른 서버로 전달.

- 흔한 패턴:
    - `/` → 프론트 정적 파일
    - `/api` → 백엔드(Spring/FastAPI)로 프록시
- 장점: 도메인 하나로 통합, CORS 단순화, 보안/로깅 중앙화
    - 프론트와 API를 같은 도메인으로 묶으면 브라우저 CORS 문제가 크게 줄어든다.

### 게이트웨이(API Gateway)

여러 백엔드로 들어가기 전 **정문(입구) 서버**.

- 라우팅, 인증/인가, 레이트리밋, 로깅/트레이싱, 변환(CORS/헤더) 등
- Nginx도 리버스 프록시로써 게이트웨이 역할을 자주 수행함

### 레이트리밋 중앙화(rate limit centralization)

각 서비스가 따로 제한을 두기보다, **앞단에서 한 번에** 정책 적용.

- 예: IP당 분당 60회, 토큰당 분당 300회
- 장점: 백엔드/AI 서비스 단순화, 공격/폭주를 입구에서 컷, 정책 변경이 쉬움

---

## 11) 실무에서 가장 자주 터지는 이슈: SPA 새로고침 404

### 왜 터지나?

SPA는 `/users/1` 같은 경로에 **실제 파일이 없음**.

서버가 그 경로를 파일로 찾다가 없으면 404를 내버린다.

### 해결: SPA fallback

“파일이 없으면 `index.html`을 내려줘라” 규칙.

- **Vercel/Netlify**: 가이드/설정(redirects, rewrite)이 비교적 쉬움
- **Nginx**: 직접 설정해야 함(핵심은 “없으면 index.html”)

---

## 12) “결국 서버가 도는 거 맞지?”에 대한 정리

맞다. 다만 역할 분담이 다르다.

- **Netlify/Vercel**
    - 빌드 서버가 플랫폼에 있고(Git push 트리거)
    - 결과물을 자기 CDN에 자동 배포
    - 필요하면 서버리스/엣지 함수로 “코드 실행”도 제공
        
        → **서버가 없다는 게 아니라, 서버 운영을 플랫폼이 감춰서 제공**하는 것
        
- **Nginx**
    - 내 EC2/컨테이너에서 Nginx 프로세스를 직접 운영
    - HTTPS/캐시/로그/업데이트/장애 대응까지 책임

---

## 13) 선택 가이드

- **Next.js + SSR/ISR/Edge + 협업/미리보기 배포 중요** → **Vercel**
- **순수 정적 사이트/SPA + 리다이렉트/헤더 설정을 빠르게 만지고 싶음** → **Netlify**
- **운영/보안/프록시/비용을 내 손으로 통제 + 백엔드/AI와 한 도메인으로 구성** → **Nginx**

---

![image.png](attachment:b4b471d2-d654-4422-819b-df26932d1ca7:image.png)

![image.png](attachment:d9f47b26-7bd4-4262-a725-281829911074:image.png)