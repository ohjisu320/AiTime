# 구현 계획
정의 :

- 시선 벡터 : 키포인트를 기반으로 하여, 양쪽 귀를 잇는 축에 직교하고 코를 통과하는 벡터
- 위치 벡터 : 화면 속에 탐지된 부모 얼굴 영역 중심점과, 아이 얼굴 영역 중심점을 잇는 벡터.
- 반응 지연 : 부모가 부른 시점부터 아동이 최초의 음성적 또는 행동적 반응을 시작하기까지의 시간으로 정의

결론 : 

1. 시선 벡터와 위치 벡터 간의 유사도를 비교하겠다.
2. 발화 자극과 행동 반응 사이의 지연 시간을 측정하겠다.
3. 발화 자극과 음성 반응 사이의 지연 시간을 측정하겠다.

→ 2, 3 을 종합하여 지표를 산출하겠다.

## 파이프라인 흐름도
```
[Input] → [Face Detect] → [Trigger Check] → [Child Analysis] → [Reaction Detect] → [Result]
   │           │                │                  │                  │               │
   ▼           ▼                ▼                  ▼                  ▼               ▼
Frame/Audio  부모/아이      호명 종료시점     ┌── Vision ─┐          복합 반응          Latency
             위치식별       T_start 기록     │ GazeVector│           판정기             산출
                                           └───────────┘              ↓
                                           ┌─ Audio ───┐         OR/AND/가중치
                                           │ VoiceReact│     
                                           └───────────┘
```             

1. **[Input]**
    - 프레임(Video) & 오디오 청크(Audio) 입력
2. **[Face Detect]**
    - 부모 / 아이 위치 식별
    - → Position Vector 생성
3. **[Trigger Check]**
    - 부모가 `이름`을 부르고 끝났는가?
    - → 호명 종료 시점 $T_{start}$ 기록
4. **[Child Analysis]**
    - (Vision) 아이의 고개 벡터 추출
        - → Gaze Vector 생성
    - (Audio) 아이 쪽에서 소리가 났는가?
5. **[Compare]**
    - Gaze Vector와 Position Vector의 각도 차이가 THRESHOLD도 이내인가?
    - **OR** 아이의 발화가 감지되었는가?
6. **[Result]**
    - 조건 만족 시 지표($T_{react}$ 기록 및 Latency 등), 모니터링 영상 산출
    - 조건 미만족시에도, 지표(NULL 값 허용)와 모니터링 영상 산출

## 필수 참고 이미지
파이프라인 시각화 : ![파이프라인 시각화](docs/pipeline.png)
지라 업무 분할 : ![지라 업무 분할 캡쳐](docs/JIRA.png)