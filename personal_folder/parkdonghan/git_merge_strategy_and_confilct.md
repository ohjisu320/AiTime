<aside>

✅ 작성자 : 박동한

✅ 작성일 : 26.01.17

</aside>

<aside>

본 문서는 **git 전략** 중 대표적인 5가지를 설명하며

팀의 git 전략이 `간소화된 git flow`로 채택된 이유를 설명한다.

추가적으로 협업에서 빈번히 발생하는 Merge 충돌에 대해 학습한다.

</aside>

<aside>

</aside>

# 1️⃣ Long-running vs Short-lived 브랜치

전략을 보기 전 브랜치는 생명 주기에 따라 나눌 수 있다.

![image.png](attachment:f3932ecd-96fb-475b-9c93-acbd41bbe54e:image.png)

## 1-1) Long-running(장수 브랜치)

- 프로젝트 생명주기 내내 유지되는 브랜치
- 예: `main/master`, `develop`, `staging`, `production`
- 특징:
    - 장수 브랜치에는 **직접 커밋하지 않고**
    - **merge/rebase 같은 “통합”을 통해서만 반영**
- 이유:
    - 테스트/리뷰를 거쳐 품질 확보
    - 릴리즈를 묶어서 계획적으로 배포하기 쉬움

## 1-2) Short-lived(단기 브랜치)

- 예: `feature`
- 특정 목적(기능/버그/리팩토링/실험)을 위해 만들고
- 통합 후 삭제
- 보통 장수 브랜치에서 분기해서 작업하고 다시 통합

---

# 2️⃣ 대표 git 전략 5가지

이제 5가지 전략을 알아보자

![출처 : https://javascript.plainenglish.io/understanding-git-branching-strategies-choosing-the-right-one-for-your-team-e509158bc207](attachment:8c96850d-93f0-4320-8571-4734f2c1a507:image.png)

출처 : https://javascript.plainenglish.io/understanding-git-branching-strategies-choosing-the-right-one-for-your-team-e509158bc207

## 2-1) 간단 정리 표

| 전략 | Long-running 브랜치 | 작업 방식 | 릴리즈/배포 표현 | 장점 | 주의점 |
| --- | --- | --- | --- | --- | --- |
| **Feature Branching** | `main` (±`develop`) | `feature/*` → PR/MR → merge | 팀마다 다름 | 가장 보편적, 리뷰/QA 좋음 | 브랜치 오래 살면 충돌/동기화 지옥 |
| **GitHub Flow** | `main`만 | 짧은 브랜치 → PR → `main` 빠른 통합 | `main` 기준 자주 배포 | 규칙 단순, 속도 빠름 | 자동 테스트 약하면 `main` 깨짐 |
| **Git Flow** | `main` + `develop` (+`release/*`,`hotfix/*`) | feature는 `develop`에서 시작/복귀 | `release/*`로 릴리즈 준비 | 릴리즈 관리 명확 | 규칙/브랜치 많아 운영 오버헤드 |
| **GitLab Flow** | `main` + (환경 or 버전 브랜치) | PR/MR 중심 + 흐름을 브랜치로 표현 | `staging→prod` 또는 `release/x.y` | 현실 운영(환경/버전) 반영 강함 | 환경/버전 브랜치 늘면 복잡해짐 |
| **Trunk-Based (TBD)** | `main`(trunk) 거의 하나 | 아주 짧은 브랜치(또는 브랜치 없이) + 자주 통합, 미완성이어도 flag 달아서 통합하거나 새로운 파일 만들어서 나중에 old code 대체. PR 없음 | feature flag로 미완성 숨김 | 통합 비용 최소, 배포 속도 최고 | 강한 CI/테스트/플래그 없으면 망함 |

## 2-2) 전략별 “흐름 그림” (ASCII 다이어그램)

- A. Feature Branching (기본형)
    
    ```
    main ──────────────┬─────────────
                       ├─ feature/A ──┐
                       └─ fix/B ──────┴─→ merge(PR)
    
    ```
    
- B. GitHub Flow (main 하나 + PR)
    
    ```
    main ─────┬─────┬─────┬────────
              ├─ feat/A ──┘
              ├─ fix/B ───┘   (PR + CI 통과 후 main에 빠르게 통합)
              └─ chore/C ─┘
    
    ```
    
- C. Git Flow (develop 중심 + release/hotfix)
    
    ```
    main     ────────────────●(tag v1.2)────────
                ▲         ┌─── release/1.2 ───┐
                │         └─────────┬─────────┘
    develop  ───┼─────┬─────────────┴────────────
                ├─ feature/A ───────┘
                └─ feature/B ───────┘
    hotfix/*: main에서 급하게 따서 main+develop에 반영
    
    develop: main에서 나오고
    feature/*: develop에서 나온다
    release: develop에서 나온다
    ```
    
- D. GitLab Flow (대표 2가지 패턴)
    - (1) 환경 브랜치 패턴
        
        ```
        main ──────────────→ staging ─────────────→ production
               (PR/MR)         (승격 merge)            (승격 merge)
        
        ```
        
    - (2) 버전/릴리즈 브랜치 패턴
        
        ```
        main ────────────┬───────────
                         └─ release/1.2 ──●(tag v1.2.3)
        
        ```
        
- E. Trunk-Based (자주 통합 + feature flag)
    
    ```
    main(trunk) ──●─●─●─●─●─●─●─●─  (항상 통합되는 중심)
       ^  짧은 브랜치(수시간~1~2일) 또는 바로 커밋
       └  미완성 기능은 feature flag로 숨김
    
    ```
    

## 2-3) 상세

- 1) Feature Branching (기능 브랜치 기반, 가장 흔한 기본형 - 운영보다는 전략과 패턴)
    
    **핵심 아이디어**
    
    - `main`(또는 `develop`) 같은 기준 브랜치에서 **기능/버그/실험마다 짧게 브랜치 따서 작업**
    - 작업 완료 후 **PR/MR로 리뷰 → 기준 브랜치에 merge**
    
    **브랜치 구성 예시**
    
    - Long-running: `main`(필수), 선택적으로 `develop`
    - Short-lived: `feature/*`, `fix/*`, `chore/*`, `experiment/*`
    
    **장점**
    
    - 작업 단위가 분리되어 **리뷰/QA/롤백/책임 추적**이 쉬움
    - 대부분의 Git 호스팅 + CI와 자연스럽게 맞음
    
    **단점/주의**
    
    - 기능 브랜치가 오래 살아남으면 **rebase/충돌/동기화 비용** 폭증
    - “큰 기능”은 PR이 커져서 리뷰가 어려워짐 → **작게 쪼개는 습관** 필요
    
    **잘 맞는 팀**
    
    - 대부분의 웹/앱 팀(중소~대규모), PR 기반 협업이 익숙한 팀
- 2) GitHub Flow (단순·린, Feature Branching의 대표 운영 방식)
    
    **핵심 아이디어**
    
    - Long-running 브랜치가 사실상 `main` **하나**
    - 모든 작업은 짧은 브랜치 → PR → `main`에 빠르게 통합
    - 릴리즈/배포는 `main` 기준으로 자주/지속적으로
    
    **브랜치 구성 예시**
    
    - Long-running: `main`
    - Short-lived: `feature/*`, `fix/*`
    - 운영: PR 필수 + CI 필수(테스트/린트)
    
    **장점**
    
    - 규칙이 단순해서 팀 합의가 쉽고 속도가 빠름
    - `main`이 항상 최신(또는 배포 가능) 상태 유지하기 좋음
    
    **단점/주의**
    
    - `main`에 자주 들어가므로 **테스트/QA 자동화가 약하면 바로 품질 사고**
    - 배포/릴리즈를 “버전 브랜치로 관리”하고 싶으면 추가 설계가 필요
    
    **잘 맞는 팀**
    
    - CI/CD 성숙도가 높고, 자주 배포하는 서비스 팀
- 3) Git Flow (구조적·규칙 많음)
    
    **핵심 아이디어**
    
    - `main`(프로덕션), `develop`(통합 개발) 2개의 장수 브랜치가 중심
    - 기능은 `develop`에서 따서 개발 후 `develop`로 합침
    - 릴리즈는 `release/*`, 긴급 수정은 `hotfix/*`로 분리 관리
    
    **브랜치 구성(전형)**
    
    - Long-running: `main`, `develop`
    - Supporting: `release/*`, `hotfix/*`
    - Short-lived: `feature/*`
    
    **장점**
    
    - 릴리즈를 “묶음/스케줄”로 관리하기 좋고 역할이 명확
    - 운영 안정성(특히 정기 릴리즈)에 유리
    
    **단점/주의**
    
    - 브랜치/규칙이 많아 **운영 오버헤드**가 큼
    - 현대적인 “자주 배포” 문화에서는 과할 수 있음
    
    **잘 맞는 팀**
    
    - 정기 릴리즈(배치형), 규제/검수 단계가 많은 환경, 모바일/패키지형 제품 팀
- 4) GitLab Flow (현실 절충형: 환경/릴리즈 관리에 강함)
    
    **핵심 아이디어(대표 형태들)**
    
    - GitHub Flow처럼 PR/MR 중심으로 단순하게 가되,
    - **배포 환경(staging/production) 또는 릴리즈(version) 흐름을 브랜치/태그로 명확히** 한다.
    
    **자주 쓰는 패턴 2가지**
    
    1. **Environment Branch 패턴**
        - `main` → `staging` → `production` 처럼 “환경 브랜치”가 존재
        - 배포 승격은 브랜치 간 merge로 표현
    2. **Release/Version Branch 패턴**
        - `main`은 다음 개발, `release/1.2` 같은 버전 브랜치로 유지보수
        - 패치가 필요하면 release 브랜치에 반영 후 태그/배포
    
    **장점**
    
    - “실제 운영 흐름(스테이징→프로덕션)”을 브랜치로 표현 가능
    - 릴리즈/핫픽스/다중 버전 유지에 유리
    
    **단점/주의**
    
    - 환경 브랜치를 늘리면 다시 복잡해질 수 있음(적정선 필요)
    
    **잘 맞는 팀**
    
    - 스테이징/프로덕션 승격이 명확한 팀, 버전별 유지보수가 있는 제품 팀
- 5) Trunk-Based Development (TBD, 트렁크 중심 개발)
    
    **핵심 아이디어**
    
    - Long-running 브랜치를 **거의 하나(trunk: main)**만 두고
    - 변경사항을 매우 자주 trunk로 통합(짧게 살고 사라지는 브랜치, 또는 브랜치 없이도)
    - 미완성 기능은 **Feature Flag(기능 토글)**로 숨긴다
    
    **브랜치 구성 예시**
    
    - Long-running: `main`(= trunk)
    - Short-lived: 아주 짧은 `feature/*` (수시간~1~2일 이내)
    - 운영: feature flag + 강한 CI + 코드리뷰(선택)
    
    **장점**
    
    - 장기 브랜치가 없어서 **큰 충돌/통합 지옥이 줄어듦**
    - 배포/릴리즈 속도가 매우 빨라짐
    
    **단점/주의**
    
    - 전제조건이 빡셈:
        - 테스트 자동화, 빠른 CI
        - 작은 단위 커밋/PR
        - feature flag 운영 능력
    - 이게 없으면 trunk가 자주 깨져서 생산성이 급락
    
    **잘 맞는 팀**
    
    - CI/CD 성숙도가 높고, 빠른 반복/배포가 중요한 팀(대규모 서비스 팀에서 자주 채택)

---

# 3️⃣ 왜 우리는 간소화된 Git Flow를 선택했는가

## 3-1) 현재 팀 상황

1. **통합 빈도와 충돌 비용이 크다 (모노레포 특성)**
    - FE/BE/AI가 한 저장소 안에서 같이 움직이면, API/스키마/공용 코드 변경이 서로 영향을 준다.
    - 통합을 늦추는 구조(장수 브랜치 다수)는 충돌과 “나중에 한꺼번에 맞추는 비용”을 크게 만든다.
    
    ⇒ **통합 브랜치 필요** (잦은 통합으로 Git 충돌, 빌드/의존성, 계약 깨짐 비용 감소)
    
2. **팀은 작지만(6명), 도메인은 3개라 조율 지점이 많다**
    - 작은 팀의 장점은 “빠른 통합”인데, 브랜치가 복잡해지면 이 장점이 사라져요.
    
    ⇒ **통합 브랜치 필요** (API/스키마/모델 출력 계약을 자주 맞추는 통합)
    
3. **main을 항상 배포 vs. 아직 QA/CI가 완벽하진 않은 현실**
    - `main`에 바로 합치는 모델(GitHub Flow/TBD)은 멋지지만
    - 전제조건(강한 테스트/feature flag/빠른 CI)이 약하면 `main`이 자주 흔들립니다.
    
    ⇒ **main 보조 장치 필요** (완충 브랜치 또는 강한 CI + 기능 기준 + PR 규칙)
    
4. **릴리즈를 ‘묶어서’ 관리할 가능성**
    - 데모/발표/배포 타이밍이 정해져 있기에 릴리즈 컷이 필요할 수 있다.
    
    ⇒ 릴리즈 컷이 필요할 때 사용할 **릴리즈 브랜치 필요** (기능 동결 + QA/버그픽스/버전업 전용)
    

## 3-2) 각 전략이 채택 되지 않은 이유

- GitHub Flow
    
    각 기술 도메인 별 통합이 필요하다. 따라서 main에 통합하는 것은 리스크가 있다.
    
- Git Flow
    - 브랜치/규칙이 많아 6명 팀에는 운영 오버헤드가 과해지기 쉽다.
    - release/hotfix 절차를 매번 엄격히 굴리다 보면 “규칙 지키다 개발이 느려지는” 상황 발
- GitLab Flow
    
    릴리즈를 묶어서 관리할 수는 있으나, GitHub Flow가 가진 문제를 가지고 있다.
    
- Trunk-Based
    
    작은 단위로 계속 trunk에 넣어도 안전한 자동화(테스트/빌드/배포)와 feature flag 문화가 필수라서 시기상조
    

## 3-3) 결론

모노레포 통합 비용을 줄이고 `main`을 보호하기 위해,

**`main` + `develop` + short-lived `feature/*`(필요 시 `release/*`)**

구조를 우선 채택한다.

<aside>

**간소화된 git flow**

</aside>

---

# 4️⃣ PR Merge 전략

브랜치 전략을 알아봤으니 우리가 채택한 방식에서 중요한 부분인 PR Merge 전략에 대해 알아보자

## 4-1) Merge commit (일반 머지)

**PR 안의 여러 커밋에 머지 커밋(PR 제목)이 추가되어 통합됨**

히스토리에 “여기서 브랜치가 합쳐졌음”이 남음.

- ✅ 장점: PR 단위가 히스토리에 명확히 남고, 원래 브랜치 구조가 보존됨
- ⚠️ 단점: PR이 많으면 그래프가 복잡해질 수 있음

**언제 좋나**

- 팀이 “브랜치 흐름을 히스토리로 남기고 싶다”
- 릴리즈/핫픽스처럼 흐름 추적이 중요할 때

---

## 4-2) Squash merge (스쿼시 머지)

**PR 안의 여러 커밋을 ‘1개 커밋’으로 압축해서 main/develop에 들어감**

히스토리가 엄청 깔끔해짐.

- ✅ 장점: main/develop 히스토리가 “PR 단위”로 깔끔해짐(잡커밋 제거)
- ⚠️ 단점: PR 내부의 세부 커밋 히스토리는 main에서 사라짐(디버깅 시 세밀 추적이 약해질 수 있음)

**언제 좋나**

- 모노레포 + 여러 팀에서 PR이 많이 올라오고, 히스토리를 깔끔히 유지하고 싶을 때

---

## 4-3) Rebase merge (리베이스 머지)

**PR 커밋들을 ‘그대로’ 유지하되, merge commit 없이 일렬로(main 위에) 붙임**

그래프가 직선에 가까워짐.

- ✅ 장점: 커밋 단위 히스토리를 유지하면서도 깔끔한 “선형 히스토리”
    
    ⇒ 커밋 단위 디버깅 가능
    
- ⚠️ 단점: 커밋이 많으면 main 히스토리가 지저분해질 수 있고(잡커밋 그대로), 경우에 따라 “히스토리 재작성” 느낌이 있어 운영 규칙이 필요
    
    ⇒ 커밋 문화와 단위가 중요함
    

**언제 좋나**

- 커밋 자체가 의미 있게 관리되고(커밋 메시지/단위가 좋고),
- “선형 히스토리”를 선호하는 팀

## 4-4) 결론

Squash merge를 유지하다가 commit 문화가 잡히면 Rebase merge로 전환

Merge commit의 경우, 모노레포이기에 히스토리를 봤을 때 꼬여있을 확률이 높아서 제외

---

# 5️⃣ Merge vs Rebase: 통합 방식의 핵심 차이

통합 브랜치에 merge가 되었다는 말은 현재 내가 작업중인 브랜치에 통합을 해야 한다는 말이다.

그 방식은 두 가지가 있다.

## 5-1) Merge

- 두 브랜치의 공통 조상 + 각 브랜치 끝점을 기준으로 합침
- 상황에 따라:
    - **Fast-forward merge**: 한쪽이 진행이 없으면 그냥 앞으로 당김(커밋 추가 없이)
    - **Merge commit**: 대부분은 새 merge commit이 생김 (두 흐름을 “매듭”처럼 연결)

## 5-2) Rebase

- “내 브랜치의 커밋들을 다른 브랜치 위로 재배치”
- 결과 히스토리가 **직선처럼 깔끔**해 보임
- 핵심 주의점:
    - rebase는 **히스토리를 다시 씀(rewrite history)**
    - 같은 내용이라도 부모가 바뀌면 **새 커밋 해시**가 생김
- 매우 중요한 규칙:
    - **공유 저장소에 이미 push한 커밋은 rebase로 rewrite 하지 마라**
    - rebase는 주로 “내 로컬 feature 브랜치 정리”에 사용

## 5-3) 결론

- **개인 feature(나만 씀, 아직 공유 안 됨)**: `rebase`로 develop 따라가기
- **공유 feature(누군가 내 feature에서 또 브랜치 땄다 / 같이 작업한다)**: `merge`로 develop 따라가기

---

# 6️⃣ Merge Conflict(머지 충돌): 언제 생기고, 정체는 뭔가

통합 브랜치를 현재 작업 중인 브랜치에 통합하는 과정에서 충돌이 발생할 수 있다.

## 6-1) 언제 발생?

“통합(integration)” 작업에서 발생 가능:

- merge, rebase(특히 interactive 포함), cherry-pick, pull, stash apply 등
- **보통 내가 작업 중인 브랜치를 최신화(통합 브랜치가 업데이트 되어서 합칠 때)할 때 발생한다.**

## 6-2) 왜 발생?

- Git이 자동으로 합치려 했는데 **서로 모순되는 변경**이 있으면 결정 못 함
- 대표 케이스:
    - 같은 줄을 서로 다르게 수정
    - 한쪽은 수정, 한쪽은 삭제 등

## 6-3) 충돌은 어떻게 알 수 있나?

- Git이 즉시 에러로 알려줌
- 그리고 `git status`에 **unmerged paths**가 표시됨
    
    → 놓치기 어렵게 설계되어 있음
    

## 6-4) “해결”만 있는 게 아니라 “취소(Abort)”도 가능

- 시간이 없거나 잘못 풀고 있다 싶으면 되돌릴 수 있음:
    - `git merge --abort`
    - `git rebase --abort`

## 6-5) 충돌 파일 내부는 이렇게 표시됨

![출처: https://velog.io/@devmin/git-conflict-solution-basic](attachment:c42fe415-2eb2-4186-8c0d-ad15b2419395:image.png)

출처: https://velog.io/@devmin/git-conflict-solution-basic

- Git이 파일 안에 구간 표시를 넣어둠:
    - 내 브랜치 내용(HEAD 쪽)
    - 구분선 `=======`
    - 상대 브랜치 내용
- 해야 할 일:
    - 표시 라인들을 정리해서 파일을 **최종적으로 원하는 형태**로 만든다
    - “내 것 / 상대 것 / 섞어서” 모두 가능 (vs code에서 익숙해져 보도록 하자)

## 6-6) 해결 후 마무리

- 충돌 해결은 결국 “변경사항”이므로
    - 파일 수정 → `git add` → `git commit`
- commit하면 Git에게 “충돌 처리 끝”이라고 알려주는 효과

---