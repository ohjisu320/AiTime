# 디렉토리 구조..
```
├── core/                         # 핵심 비즈니스 로직
    ├── __init__.py
    ├── vector_math.py            # 벡터 연산 (시선 / 위치 벡터)
    ├── angle_calculator.py       # 각도 계산
    ├── latency_tracker.py        # 반응 지연 추적
    ├── trial_manager.py          # 시도 관리
    │
    └── reaction/                 # 반응 판정 시스템
        ├── __init__.py
        ├── base.py               # 반응 판정기 인터페이스
        ├── gaze_detector.py
        ├── voice_detector.py
        ├── composite.py          # OR/AND/가중치 조합
        ├── events.py             # 반응 이벤트 정의
        └── factory.py            # 판정기 팩토리
```