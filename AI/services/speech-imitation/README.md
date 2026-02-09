# Speech Imitation Service (발화 모방 평가)

아기의 발화 모방 능력을 평가.

부모(성인)가 특정 단어를 말하면(자극), 아기가 이를 따라 말하는지(반응)를 분석하고 그 유사도를 평가.

## 🚀 파이프라인 흐름 (Pipeline Architecture)

`Orchestrator`를 통해 6단계의 순차적인 스테이지(Pipeline Stage)로 실행됨

### 1. InputStage (`input_stage.py`)
- **역할**: 비디오 파일 입력 → 오디오 추출(FFmpeg) 및 로드(Librosa/Torchaudio).
- **출력**: `context.audio` (16kHz Mono)

### 2. VadStage (`vad_stage.py`)
- **역할**: 음성 활동 감지 (Voice Activity Detection).
- **핵심 기술**: Silero VAD 사용.
- **설정**: 
  - `VAD_MIN_SILENCE_DURATION_MS = 10ms` (짧은 침묵도 감지하여 정밀 분리)
  - `VAD_MIN_SPEECH_DURATION_MS = 50ms` (짧은 옹알이도 포착)
- **목표**: 성인의 자극과 아기의 반응이 뭉쳐있지 않고 개별 세그먼트로 분리되도록 함.

### 3. SpeakerStage (`speaker_stage.py`)
- **역할**: 감지된 음성 세그먼트의 화자(성인/아기) 추정.
- **전략**: Pitch(F0) 기반 분류를 시도하지만, 데이터 특성상(아기 목소리가 더 낮거나 겹침) 불안정할 경우 **모든 세그먼트를 후보군으로 수집**하여 다음 단계로 넘김.

### 4. TrialPlanStage (`trial_plan_stage.py`)
- **역할**: 아기의 월령(12~23개월)에 맞는 자극 단어 세트(Stimulus Set) 계획 수립.
- **예시**: 18개월 → "이모", "할머니", "할아버지", "삼촌" (총 4 Trial)

### 5. ImitationJudgeStage (`imitation_judge_stage.py`)
- **역할**: 실제 오디오 세그먼트와 계획된 Trial을 매칭하고 유사도를 평가.
- **매칭 전략 (Alternating Strategy)**:
  - 화자 분류가 어려울 경우, "자극 → 반응"이 순차적으로 이루어진다는 대화의 특성을 활용.
  - 시간순으로 나열된 오디오 세그먼트를 `Stimulus(0) -> Response(1) -> Stimulus(2) -> Response(3)...` 순서로 강제 할당.
- **유사도 평가**:
  - **MFCC + DTW**: 텍스트 변환(STT) 없이 오디오 파형 자체의 특징을 비교하여 발음의 유사성을 0~1 점수로 산출.

### 6. ResultStage (`result_stage.py`)
- **역할**: 최종 분석 결과를 JSON 형태로 정형화하여 반환.

---

## 📂 프로젝트 구조

```
AI/services/speech-imitation/
├── app/
│   ├── config.py            # 설정 (VAD 파라미터, 임계값 등)
│   ├── main.py              # 진입점 (CLI 및 실행)
│   ├── models/              # AI 모델 래퍼
│   │   ├── vad.py           # Silero VAD
│   │   ├── speaker_splitter.py # Pitch 추출 및 화자 분리
│   │   └── imitation_similarity.py # MFCC+DTW 유사도 계산
│   ├── pipeline/
│   │   ├── orchestrator.py  # 파이프라인 전체 실행 관리
│   │   ├── context.py       # 데이터 공유 객체
│   │   └── stages/          # 개별 스테이지 구현
│   └── utils/
│       ├── audio.py         # 오디오 로드/저장/전처리
│       └── logger.py        # 로깅 설정
└── README.md
```

## ⚙️ 설정 (Configuration)

`app/config.py`에서 주요 파라미터를 조정

- **VAD 설정**: 분리력을 높이기 위해 `VAD_MIN_SILENCE_DURATION_MS`를 작게(10~30ms) 설정
- **매칭 설정**: `PITCH_CHILD_HZ_THRESHOLD` 조정을 통해 화자 분리 민감도를 제어

## ▶️ 실행 방법

```bash
# 비디오 파일 경로와 월령을 입력하여 실행
python -m app.main --video /path/to/video.mp4 --age-months 18
```

## 🔍 디버깅

- `debug_output/` 폴더에 각 Trial별로 매칭된 `stim.wav`(자극)와 `resp.wav`(반응) 파일이 저장됨
- 이를 통해 매칭이 올바르게 되었는지(순서 밀림 확인 등) 청취하여 검증 가능
