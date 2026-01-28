# 디렉토리 구조..
```
├── pipeline/                            # 분석 파이프라인
    ├── __init__.py
    ├── orchestrator.py                  # 파이프라인 오케스트레이터
    ├── stages/
    │   ├── __init__.py
    │   ├── input_stage.py               # 입력 처리 (영상/음성 분리)
    │   ├── face_detect_stage.py         # 얼굴 탐지 & 위치 벡터
    │   ├── trigger_stage.py             # 호명 트리거 탐지
    │   ├── child_analysis_stage.py      # 아이 분석 :  Vision + Audio 통합
    │   ├── reaction_detect_stage.py     # 복합 반응 판정
    │   └── result_stage.py              # 결과 집계
    └── context.py                       # 파이프라인 컨텍스트
```