# 음성 모방(Speech Imitation) 서비스 분석 및 최적화 보고서

## 1. 현재 구현 분석

### **1.1 실행 순서 (Pipeline)**
이 서비스는 다음과 같은 단계로 비디오를 처리합니다:

Input → VAD → Speaker → TrialPlan → ImitationJudge → Result → Visualization

1.  **입력 (`worker.py`)**:
    -   RabbitMQ를 통해 분석 요청을 수신합니다.
    -   S3(Presigned URL)에서 비디오를 다운로드합니다.
2.  **VAD 단계 (`vad_stage.py`)**:
    -   **알고리즘**: **Silero VAD** (딥러닝 기반, 최신 기술).
    -   **Fallback**: Silero 로드 실패 시 에너지(RMS) 기반 방식 사용.
    -   **목적**: 침묵이나 잡음을 제외하고, 실제 "말소리"가 있는 구간만 탐지합니다.
3.  **화자 분리 단계 (`speaker_stage.py`)**:
    -   **알고리즘**: **Pitch(음높이) 임계값 기반 휴리스틱**.
    -   **방식**: `librosa.pyin` 알고리즘을 사용하여 성대 떨림(F0)을 추출합니다.
    -   **로직**:
        -   평균 음높이가 설정값(**200Hz**, `config.py` 기준)보다 높으면 **아이(Child)**.
        -   낮으면 **어른(Adult)**으로 분류합니다. (문서 예시는 400Hz였으나 실제 코드는 200Hz로 매우 낮게 잡혀있음)
    -   **필터링**: 발화 길이(Duration)를 기준으로 너무 짧거나 긴 구간을 제외하여 후보군을 선정합니다.
4.  **시도 계획 단계 (`trial_plan_stage.py`)**:
    -   **검사 설계(Planning)**: `REPETITIONS_PER_TRIAL=1` 설정에 따라 trial 구조(자극 목록, 반복 횟수, ID 부여)를 구성합니다.
5.  **모방 판정 단계 (`imitation_judge_stage.py`)**:
    -   **전략**: **교차 할당(Alternating) 가정**.
        -   어른과 아이의 발화가 시간순으로 `[자극(엄마) -> 반응(아이) -> 자극 -> 반응...]` 순서로 나타날 것이라고 강제 가정합니다.
        -   **반복 횟수**: 코드상 `REPETITIONS_PER_TRIAL = 1`로 설정되어 있어, 한 번의 자극에 한 번의 반응만 기대합니다. (문서상 x3회 반복 의도와 불일치)
        -   *문제점*: 아이가 대답하지 않거나, 엄마가 연속으로 두 번 말하면 순서가 꼬여 엉뚱한 구간끼리 비교하게 됩니다.
    -   **유사도 측정**: **MFCC + DTW** (`imitation_similarity.py`).
        -   소리의 특징(MFCC)을 추출하고, 시간 축을 늘이거나 줄여서(DTW) 두 소리의 패턴이 얼마나 비슷한지 0~1 점수로 계산합니다.
    -   **운율(Prosody) 및 이상음 감지**:
        -   **Squeal(끼익 소리)**: 전체 소리 중 고음(Squeal Threshold 이상) 비율을 체크합니다.
        -   **단조로움(Monotony)**: 음높이의 변화폭(MAD, Mean Absolute Deviation)을 계산합니다.
        -   **로직**: 변화폭이 너무 작으면 "단조로움(Monotone)", 너무 크면 "노래/과장됨"으로 판정합니다.
6.  **결과 처리 단계 (`result_stage.py`)**:
    -   `PipelineContext`의 데이터를 최종 결과에 필요한 형태(스키마 버전, 실패 분류 등)로 정규화합니다.
7.  **시각화 단계 (`visualization_stage.py`)**:
    -   **OpenCV**(`cv2`)와 **Pillow**(`PIL`)를 사용하여 원본 영상 위에 분석 결과(성공 여부, 별점, 텍스트)를 덧입혀 저장합니다.
8.  **출력 단계 (`worker.py`)**:
    -   정규화된 데이터를 최종 JSON 메시지 스키마로 직렬화(Serialize)하고 RabbitMQ로 발행(Publish)합니다.

---

## 2. 스테이지별 상세 분석 (Dossier)

각 단계의 기술 선택, 예산(Latency/Memory), 실패 모드를 정량적으로 분석했습니다.

### **2.1 VAD & Speaker Stage (음성 감지 및 화자 분리)**

| 항목 | 내용 |
| :--- | :--- |
| **Purpose** | 전체 오디오에서 "누가(엄마/아기), 언제" 말했는지 식별 |
| **Why this tech** | **Silero VAD (현행)**: SOTA, 경량, 정확함 (ONNX 가능)<br>**Pitch Heuristic (현행)**: 단순 구현 가능하나 정확도 낮음 |
| **Inputs/Outputs** | Input: Raw Audio (PCM Float32, 16kHz)<br>Output: `List[LabeledSegment]` (start, end, speaker_label, **acoustic_metrics**, **quality_flags**) |
| **Latency Budget** | **Target(p50)**: < 500ms, **Target(p95)**: < 1.0s (1분 영상 기준)<br>- *Rationale: SLO(10s) 분배: VAD/Split(1s) + Analysis(3s) + Network/Margin(6s)*<br>**Current**: **~30s (Estimated)** (`pyin` 병목)<br>**Worst**: 시간 초과 (긴 영상) |
| **Memory Budget** | **Target**: < 500MB<br>**Current**: 실측 필요 (`pyin` Viterbi 연산 시 급증 우려) |
| **Compute Estimate** | `pyin`: $O(N \times States^2)$ (비터비) → **CPU 부하 극심** |
| **Failure Modes** | 1. **Octave Error**: 아기 목소리(High Pitch)를 노이즈나 어른으로 오인<br>2. **Parentese**: 엄마의 높은 톤을 아기로 오인<br>3. **Noise**: 잡음 환경에서 `pyin` 추출 실패 |
| **Observability** | VAD 감지 비율, Speaker별 발화 시간 비율 (Pitch Confidence 없음) |

### **2.2 Imitation Judge Stage (모방 판정)**

| 항목 | 내용 |
| :--- | :--- |
| **Purpose** | 엄마의 자극과 아기의 반응이 얼마나 유사한지, 아기 목소리가 정상인지 판정 |
| **Why this tech** | **MFCC+DTW (현행)**: 딥러닝 없이 유사도 측정 가능 (레거시)<br>**Alternating (현행)**: 화자 분리 실패를 가정하고 순서로 떄려맞춤 |
| **Inputs/Outputs** | Input: Stimulus Audio, Response Audio<br>Output: Similarity(0~1), Prosody Metrics |
| **Latency Budget** | **Target**: < 100ms per pair<br>**Current**: **클립이 짧게 잘릴 때는 빠름**, 길어지면 비용 급증(→ band 필요) |
| **Failure Modes** | 1. **Alignment Fail**: 아기가 침묵하면 엄마끼리 비교 (치명적)<br>2. **Monotony Miss**: 로봇/거친 목소리를 "정상(변동 있음)"으로 오판<br>3. **Noise Sensitive**: 배경 잡음이 유사도를 깎아먹음 |
| **Observability** | 평균 유사도, DTW Cost, Squeal/MAD 분포, 판정 실패 사유 통계 |

---

## 3. 한계점 및 "이상한 소리/단조로움" 문제

사용자님의 목표인 *"아이가 제대로 답했는지도 중요하지만, 단조롭거나 괴상한 소리를 내는지 확인하는 것"* 에 대한 현재 시스템의 한계입니다.

### **3.1 단조로움(Monotony) 감지의 한계와 원인 분석**

**문제의 진원지**: `SpeakerStage` 및 `ImitationJudgeStage` 내의 **Pitch(음높이) 분석 로직**

1.  **MAD(평균 절대 편차) 방식의 근본적 한계**
    -   **현재 로직**: `librosa.pyin`으로 추출한 음높이(F0) 값들의 **MAD (Mean Absolute Deviation, Semitone Domain)**만 계산합니다. "음높이가 얼마나 오르락내리락하는가"만 봅니다.
    -   **실제 문제**: 자폐 스펙트럼(ASD) 아동이나 발달 지연 아동의 "단조로움"은 단순히 음높이 변화가 없는 것뿐만 아니라, **음질(Voice Quality)**의 문제입니다.
        -   **기계적인 목소리(Robotic)**: 음높이 변화는 있어도 성대의 진동이 불규칙(Jitter)하거나 소리가 거칠 수 있습니다. 현재 로직은 이를 감지할 수 없습니다.
        -   **바람 빠지는 소리(Breathiness)**: 성대가 완전히 닫히지 않아 공기 소리가 섞이는 경우입니다. 이는 `Shimmer` 지표로 봐야 하는데, 현재는 구현되어 있지 않습니다.
    -   **결과**: 아이가 억양 없이 로봇처럼 말해도, 소리 자체의 노이즈 때문에 음높이 추정값이 튀어서 "변화가 크다(정상/과장됨)"라고 **오판**할 확률이 매우 높습니다.

2.  **`librosa.pyin` 알고리즘의 한계**
    -   `pyin`은 확률적 알고리즘이라 잡음에 민감합니다. 아이 목소리가 조금만 갈라지거나 배경음이 섞이면 **옥타브 오류(Octave Error)**가 발생합니다. (예: 실제 200Hz인데 100Hz나 400Hz로 튐)
    -   이 튀는 값들이 MAD(변동폭) 계산에 포함되면, 실제로는 단조로운 목소리인데도 **수치상으로는 매우 다이내믹한 목소리**로 둔갑하게 됩니다.

### **3.2 "괴상한 소리" 감지 부족의 원인**

**문제의 진원지**: `ImitationJudgeStage`의 단순 임계값 로직

    -   **치명적 로직 (Prosody Gate)**: 현재 `BAD_PROSODY`는 **`F0 > 450Hz` 조건이 참일 때만 발동**합니다. 즉, 저음/중음 대역에서 발생하는 "로봇 같은 목소리(단조로움)"는 아예 검사조차 하지 않고 통과됩니다. 이는 "단조로움 감지"라는 목표와 정면으로 배치됩니다.
    -   **해결책**:
        -   고음(Squeal)과 단조로움(Monotony) 감지를 분리해야 합니다.
        -   `Parselmouth` 등을 통해 스펙트럼 전체 특성을 봐야 합니다.
    -   **Spec Proposal**:

        -   `VOICE_QUALITY_ODD` 같은 모호한 플래그 대신, **`LOW_HNR` (거친 소리)**, **`LOW_VOICING` (속삭임/기식음)** 등 원인이 명확한 하위 지표로 쪼개어 저장합니다.
        -   A3 점수 산출 시 `SQUEAL`, `MONOTONE`과 함께 위 정밀 지표들을 조합하여 가중치를 부여합니다.

### **3.3 성능 병목의 상세 원인 (EC2 CPU)**
1.  **`librosa.pyin`의 비효율성**
    -   이 알고리즘은 내부적으로 **Viterbi(비터비)** 알고리즘을 수행하여 가능한 모든 음높이 경로를 탐색합니다.
    -   순수 Python + NumPy로 구현되어 있어, C++로 최적화된 라이브러리(Parselmouth/Praat) 대비 연산량이 압도적으로 많습니다.
    -   긴 영상(1분 이상) 처리 시, 이 단계 하나가 전체 처리 시간의 **70~80%**를 잡아먹을 것으로 예상됩니다.

---

## 4. 현대화 및 최적화 전략 (EC2 CPU 환경 최적)

**타겟 환경**: AWS EC2 (Xeon v4, AVX2 지원, **GPU 없음**)

각 최적화 제안별로 **GPU 권장(이상적)**, **CPU 가능(현실적)**, 그리고 **현 타겟 환경에서의 실행 가능성**을 분석했습니다.

### **4.1 최적화 1: `librosa.pyin` 대체 (단조로움/이상음 해결)**

| 옵션 | 도구 | 특징 | 하드웨어 요구 | 타겟 환경 적합성 |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (CPU)** | **Parselmouth (Praat)** | - C++ 기반, 매우 빠름<br>- Jitter/Shimmer/HNR 등 음질 지표 제공 | **CPU (1 core)** | **✅ 최적 (강력 추천)**<br>가장 빠르고 가벼움. |
| **Option B (GPU)** | TorchAudio / CREPE | - 딥러닝 기반 Pitch Tracking<br>- 잡음에 매우 강함 | GPU 권장 | ❌ 부적합<br>CPU에서는 `pyin`만큼 느릴 수 있음. |
| **Option C (CPU)** | OpenSMILE | - 감정/음질 분석 표준<br>- 방대한 피처 추출 (eGeMAPS) | CPU | ⚠️ 가능하나 무거움<br>설치/설정이 복잡함. |

> **결론**: **Parselmouth**가 가장 현실적인 대안입니다. 영유아 음성의 불안정성을 고려하여 Golden Set에서의 검증이 필요하지만, CPU 환경에서 Voice Quality 지표를 얻을 수 있는 가장 효율적인 방법입니다.

### **4.2 최적화 2: 화자 분리 (Speaker Diarization)**

| 옵션 | 도구 | 특징 | 하드웨어 요구 | 타겟 환경 적합성 |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (GPU)** | **PyAnnote Audio** | - 현재 SOTA (가장 정확함)<br>- 겹치는 소리 분리 가능 | **GPU 필수** | ❌ 불가<br>CPU에서 돌리면 1분 영상에 1분 이상 소요됨. |
| **Option B (CPU)** | **ONNX 임베딩 (ECAPA-TDNN)** | - 경량화된 모델로 성문(Voiceprint)만 추출<br>- 이후 Cosine Similarity로 군집화<br>- *PyAnnote/NeMo 모델의 ONNX 최적화 버전 활용 가능* | **CPU (AVX2)** | **✅ 최적 (구현 난이도 중)**<br>ONNX Runtime + Quantization 사용 시 CPU에서 실시간 가능. |
| **Option C (CPU)** | 개선된 휴리스틱 (Formant) | - Pitch 외에 Formant(음색) 정보 추가<br>- Parselmouth로 추출 가능 | CPU | ⚠️ 대안<br>딥러닝보다 정확도는 낮지만 매우 빠름. |

> **결론**: **Option B (ONNX 임베딩)**를 추천합니다.
> *   **왜 SpeechBrain인가?**: PyAnnote나 NeMo는 무거운 파이프라인/프레임워크 종속성이 있어 ONNX 변환이 까다롭거나 모델이 큽니다. 반면 **SpeechBrain의 ECAPA-TDNN**은 단일 모델로 매우 가볍고(20MB), ONNX 변환 레퍼런스가 풍부하여 CPU 배포에 최적입니다.
> *   `speechbrain/spkrec-ecapa-voxceleb` 모델을 ONNX로 변환하여 사용합니다.

### **4.3 최적화 3: 유사도 알고리즘 (Similarity)**

| 옵션 | 도구 | 특징 | 하드웨어 요구 | 타겟 환경 적합성 |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (GPU)** | **Wav2Vec2 300M (Large)** | - 가장 정확한 언어적 유사도<br>- 미세한 발음 차이 구분 가능 | **GPU 필수** | ❌ 불가<br>CPU에서 너무 느림. |
| **Option B (CPU)** | **Wav2Vec2 / HuBERT (Base, Quantized)** | - 8-bit 양자화된 베이스 모델<br>- 정확도 준수, 속도 빠름 | **CPU (AVX2)** | **✅ 최적**<br>ONNX Runtime의 q8(Quantized) 모델 사용 시 CPU에서 원활. |
| **Option C (Legacy)** | MFCC + Noise Reduction | - 기존 방식에 잡음 제거 전처리 추가<br>- 구현 쉬움 | CPU | ⚠️ 차선책<br>근본적인 잡음 취약성 해결 안 됨. |

> **결론**: **Option B (Quantized Wav2Vec2 ONNX)** 도입을 목표로 하되, 단기적으로는 **Option C**로 방어할 수 있습니다.


### **4.4 시스템 아키텍처 최적화 (ONNX vs OpenVINO)**

CPU(Intel Xeon) 환경에서 딥러닝 모델 추론 속도를 높이는 핵심 기술 두 가지를 비교하셨습니다.

| 비교 항목 | **ONNX Runtime (ORT)** | **OpenVINO (Intel)** |
| :--- | :--- | :--- |
| **최적화 대상** | 범용 (CPU, GPU, NPU 등) | **Intel CPU/GPU/NPU 특화** |
| **속도 (Intel CPU)** | 빠름 (AVX2 활용) | **매우 빠름** (Intel 하드웨어 극한 최적화) |
| **호환성** | PyTorch 내보내기가 표준화됨 | ONNX 모델을 한 번 더 변환(IR)해야 함 |
| **구현 난이도** | 쉬움 (`pip install onnxruntime`) | 중간 (`openvino-dev` 등 설정 필요) |

-   **결론 (타겟 환경: Xeon v4)**:
    -   **OpenVINO**가 Intel CPU(특히 구형 Xeon)에서는 ONNX Runtime보다 더 빠를 수 있으며, 실제 이득은 **마이크로벤치로 확인**해야 합니다.
    -   하지만 **ONNX Runtime**이 배포/관리(Docker 이미지 크기, 코드 복잡도) 면에서 훨씬 간편합니다.
    -   **전략**: **1단계는 ONNX Runtime**으로 전환하여 안정성을 확보하고, 만약 그래도 속도가 부족하면 **2단계로 OpenVINO**를 적용하는 것을 권장합니다.

### **4.5 병렬 처리 구조 (Latency)**
-   **문제**: `worker.py`는 다운로드 -> 분석 -> 결과 전송을 순차적으로 수행하며, `prefetch_count=1`로 설정되어 있습니다.
-   **비효율성**: 분석(CPU)이 돌아가는 동안 네트워크(다운로드/업로드) 대역폭은 놉니다.
-   **개선안**: 파이프라인을 **비동기 스트리밍** 구조로 바꾸거나, 적어도 S3 다운로드와 분석을 병렬화(Producer-Consumer 패턴)하면 처리량(Throughput)을 높일 수 있습니다.

---

## 5. 파이프라인 구조적 한계 및 비효율성 분석

단순히 각 단계의 "성능(정확도/속도)"을 높이는 것을 넘어, **전체 파이프라인의 흐름(Flow)** 자체가 가지는 논리적 모순과 비효율성을 발견했습니다.

### **5.1 "교차 할당(Alternating)" 로직의 치명적 결함**
-   **현재 로직**: `ImitationJudgeStage`는 모든 발화 구간을 시간순으로 나열한 뒤, 무조건 `[엄마 -> 아기 -> 엄마 -> 아기]` 순서라고 가정하고 짝을 짓습니다.
-   **치명적 문제**:
    -   아기가 대답을 안 하고 침묵하면? → 다음 엄마의 말을 "아기의 대답"으로 인식하여 엄마 소리끼리 비교합니다. (유사도 낮음, 실패 처리되지만 논리 자체가 꼬임)
    -   엄마가 "아가야~" 하고 쉬었다가 "따라해봐~"라고 두 번 말하면? → 두 번째 엄마 말을 "아기 대답"으로 오인합니다.
    -   **결과**: VAD와 화자 분리가 아무리 완벽해도, 이 "순서 끼워맞추기" 로직 때문에 전체 평가는 엉망이 될 수밖에 없습니다.
-   **개선안**: **"Event-based Matching"**
    -   엄마(Stimulus)의 발화가 끝나면, `RESPONSE_TIMEOUT` 이내에 시작되는 **"아기(Child)" 라벨이 붙은 발화**만을 검색해서 매칭해야 합니다. 순서가 아니라 **조건(Time Window + Speaker Label)** 기반으로 변경해야 합니다.

### **5.2 독립적인 단계(Stage) 간 정보 단절**
-   **문제**: `SpeakerStage`에서 이미 "이 구간은 어른이다/아이다"라고 힘들게 분류했는데, `ImitationJudgeStage`에서는 이 라벨을 무시하고 시간 순서대로 다시 섞어서 추론합니다. 앞 단계의 분석 결과가 뒤 단계에서 제대로 활용되지 않고 있습니다.
-   **비효율성**: 화자 분리 단계의 연산 자원을 낭비하는 꼴입니다.

### **5.3 직렬 처리 구조 (Latency) [후순위]**
-   **문제**: `worker.py`는 다운로드 -> 분석 -> 결과 전송을 순차적으로 수행하며, `prefetch_count=1`로 설정되어 있습니다.
-   **현황**: 현재 단계에서는 분석 속도 자체(CPU 병목)를 해결하는 것이 급선무이므로, 이 아키텍처 개선은 **후순위(Low Priority)**로 미둡니다.


---

## 6. 개선 옵션 카드 (Option Cards)

세 가지 트랙으로 나누어 제안합니다.

### **Track 1: Quick Win (보수적 접근 - 당장 적용)**
*   **변경 내용**:
    *   `librosa.pyin` → **Parselmouth (Praat)** 또는 **PyWorld (Harvest)** 교체
    *   **DTW 최적화**: `Sakoe-Chiba Band` 적용 (Radius 제한)
*   **기대 효과**:
    *   **Latency**: 10배 이상 감소 (50s → 5s)
    *   **Quality**: Jitter/Shimmer로 단조로움/이상음 정확히 감지
*   **CPU 가능성**: **Yes (1 Core 충분)**
*   **구현 난이도**: **Low** (라이브러리 교체 수준)
*   **리스크**: 기존 Pitch 값과 스케일이 다를 수 있음 (Threshold 재조정 필요)

### **Track 2: Realistic Refactoring (중간 - 권장)**
*   **변경 내용**:
    *   **Silero VAD ONNX** 도입 (Torch 의존성 제거 및 속도 향상)
    *   **Protocol-based Matching** 로직 변경 (순서 강제 폐기 → 조건 검색)
*   **기대 효과**:
    *   **Accuracy**: 순서 꼬임 문제 완벽 해결
    *   **Stability**: 긴 영상 처리 시 타임아웃 방지
*   **CPU 가능성**: **Yes (AVX2 활용)**
*   **구현 난이도**: **Mid** (로직 재설계 필요)
*   **리스크**: 로직 변경 시 기존 테스트 케이스(예: 침묵 시나리오) 깨질 수 있음

### **Track 2.1 상세: Protocol-based Matching 로직 (Alternating 폐기)**

"순서 강제(Alternating)"와 "조건 검색(Protocol-based)"의 차이를 구체적으로 설명합니다.

#### **(1) 현재: Alternating (순서 끼워맞추기)**
*   **로직**: 모든 발화 세그먼트를 시간순으로 나열하고 `[0, 1], [2, 3], [4, 5]...` 짝을 짓습니다.
*   **문제 상황 (시나리오)**:
    1.  **엄마**: "아가야~" (Seg 0)
    2.  **아기**: (침묵)
    3.  **엄마**: "따라해봐~" (Seg 1)
    *   **결과**: `Seg 0`과 `Seg 1`을 비교합니다. **엄마 목소리끼리 비교**하므로 유사도가 낮게 나오고, "아기가 이상하게 말했다"고 오판할 수 있습니다.

#### **(2) 개선: Protocol-based Matching (조건 검색)**
*   **로직**:
    1.  **StimulusAnchor**: 화자 분리를 통해 확실한 **"엄마(Adult)"** 구간을 먼저 찾습니다. (이게 기준점입니다)
    2.  **SearchWindow**: 엄마 발화 시작 시점(`Stimulus Onset`)부터 **`RESPONSE_TIMEOUT` (예: 5초)** 구간을 설정하되, **Trial 8초** 경계에서 종료합니다.
    3.  **FilteredSelect**: Window 내에 존재하는 세그먼트 중 **"아기(Child)" 라벨**이 붙은 것만 후보로 올립니다.
        *   후보가 없으면? → `NO_RESPONSE` (명확한 침묵 판정)
        *   후보가 여러 개면? → 가장 긴 것 또는 유사도가 높은 것을 선택 (Noise 필터링)

> **이점**: 아기가 침묵하거나 옹알이를 여러 번 해도, **"엄마의 자극에 대한 반응"**이라는 인과관계를 정확히 추적할 수 있습니다.

### **Track 2 완료 시점의 변화 (Before vs After)**

Track 1(Quick Win)과 Track 2(Realistic Refactoring)를 모두 적용했을 때의 변화를 요약합니다. **"느리고 멍청한 순서 맞추기"**에서 **"빠르고 똑똑한 조건 검색"**으로 진화합니다.

| 구분 | **현재 (AS-IS)** | **Track 2 적용 후 (TO-BE)** |
| :--- | :--- | :--- |
| **VAD (음성 감지)** | **Silero VAD (Torch Hub)**<br>- 콜드 스타트 시 다운로드 발생<br>- 무거운 PyTorch 의존성 | **Silero VAD (ONNX Local)**<br>- 로컬 모델 파일 사용 (인터넷 X)<br>- 가볍고 빠른 추론 엔진 |
| **Pitch (음높이)** | **librosa.pyin** (Python)<br>- 확률적 추정 (느림, 부정확)<br>- 1분 영상에 **30~50초 (Estimated)** 소요 | **Parselmouth (Praat C++)**<br>- 자기상관(Autocorrelation) (매우 빠름)<br>- 1분 영상에 **1초 미만 (Estimated)** 소요 |
| **Speaker (화자 분리)** | **단순 Pitch 임계값 (Rule)**<br>- "200Hz 넘으면 애기"<br>- 성인 여성/저음 아기 구분 불가 | **(유지하되 정확도 향상)**<br>- `Parselmouth`의 정확한 Pitch + `Formant` 정보 활용<br>- *(딥러닝 모델 도입은 Phase 3)* |
| **Matching (짝짓기)** | **무조건 교차 (Alternating)**<br>- 엄→애→엄→애 순서 강제<br>- 아기가 침묵하면 다음 엄마 말과 매칭됨 | **조건 검색 (Protocol-based)**<br>- 엄마 시작 후 5초(+Clamp) 내 아기 찾기<br>- 침묵 시 확실하게 `NO_RESPONSE` 처리 |
| **Prosody (단조로움)** | **단순 높낮이 변동 (MAD)**<br>- 로봇 소리여도 음이 튀면 "정상" 오판<br>- 고음(450Hz+)만 검사하는 버그 | **음질 분석 (Voice Quality)**<br>- **Jitter/Shimmer**로 성대 진동 불규칙성 감지<br>- 저음/고음 관계없이 모든 구간 검사 |
| **Similarity (유사도)** | **MFCC + DTW (Full Search)**<br>- 모든 프레임 전수 비교<br>- 긴 문장에서 느려짐 | **MFCC + DTW (Sakoe-Chiba)**<br>- 대각선 주변만 검색 (반경 제한)<br>- 정확도는 유지하고 속도 **2배 이상** 향상 |

### **Track 3: Bold Architecture (공격적 접근 - 장기) [High Complexity / Conditional]**
*   **변경 내용**:
    *   **Feature Extraction**: `openSMILE` / `eGeMAPS` 도입 (음성 병리 분석 표준)
    *   **Model**: LightGBM/LogReg 등 **경량 분류기**로 이상음(Squeal, Monotony) 다중 분류
*   **기대 효과**:
    *   **Accuracy**: 사람 수준의 화자 구분 및 발음 유사도 측정
    *   **Robustness**: 잡음 환경에서도 강건함
*   **CPU 가능성**: **Conditional** (Quantization 필수, 동시 처리량 제한)
*   **구현 난이도**: **High** (모델 변환 및 최적화 필요)
*   **리스크**: 모델 로딩 시간 및 메모리 사용량 증가 (OOM 주의). **Track 1(Parselmouth)만으로 해결되지 않을 경우에만 고려해야 합니다.**

---

## 7. 벤치마크 및 검증 계획 (Verification Plan)

**1. 성능(Latency) 측정**
*   **대상**: 1분, 3분, 5분 길이의 테스트 영상 (S3 Presigned URL)
*   **지표**: `Total Processing Time`, `VAD Time`, `Pitch Extraction Time`
*   **성공 기준**: 1분 영상 처리 < **10초** (EC2 c4.xlarge 기준)

**2. 정확도(Accuracy) 측정 (Golden Sample)**
*   **데이터셋**:
    *   CASE A: 정상 발화 (엄마-아기 교대)
    *   CASE B: 아기 침묵 (엄마만 말함)
    *   CASE C: 단조로운/이상한 목소리 (병리적 샘플)
*   **지표**:
    *   **화자 분리 정확도**: (정답 구간 / 예측 구간) IoU
    *   **이상음 감지율**: (감지된 이상음 / 실제 이상음) Recall
*   **성공 기준**: CASE B에서 오탐 0건, CASE C에서 Recall > 80%

---

## 8. 결론 및 제안

1.  **즉시 적용 (Quick Win)**: `librosa.pyin`을 **Parselmouth(Praat)**로 교체하십시오. 속도가 획기적으로 빨라지고, **Jitter/Shimmer** 데이터를 통해 단조로움/이상한 소리 감지 능력이 대폭 향상됩니다.
2.  **로직 수정**: "엄마 다음엔 무조건 아기"라는 강제 순서 가정을 버리고, 화자 분리 정확도를 높여서 "아기 목소리가 들린 구간"을 찾아 자극과 매칭하는 방식으로 변경해야 합니다.
3.  **단계적 도입**:
    -   **1단계**: Parselmouth 도입 + ONNX Runtime 적용 (속도/단조로움 해결)
    -   **2단계**: 화자 분리 모델 도입 + 파이프라인 로직 수정 (정확도 해결)

---

## 9. Actionable Backlog (JIRA Style - AI Dev Standard)

AI Dev Agent 표준(Repro Keys, Stage Contract)을 준수하며, 즉시 실행 가능한 티켓 형태로 정리했습니다.

### **Phase 1: Quick Win (기반 마련 및 긴급 수정)**

#### **[AI-409] 성능 수치 계측 전환 (추정 → 실측)**
*   **User Story**: 문서상의 "30초 소요" 같은 추정치 대신, 실제 스테이지별 소요 시간을 로그로 남겨 정확히 파악한다. 이것이 선행되어야 이후 최적화의 효과를 증명할 수 있다.
*   **AC**:
    1.  `Orchestrator` 실행 완료 시 `context.processing_times`를 파싱하여 로그에 출력한다.
    2.  1분/3분/5분 영상에 대한 Stage별 `p50`, `p95` Latency 리포트를 생성한다.
    3.  **Distribution Report**: `pitch`, `HNR`, `voiced_fraction`의 p50/p95 분포 및 이상음 발생률을 함께 리포트한다.
    4.  **Artifact**: `artifacts/benchmarks/<date>/speech_imitation_latency.jsonl` (Run ID 포함, Per-run + Global 집계).

#### **[AI-410] Stage Contract v1 (Segment & Pair Schema)**
*   **User Story**: `SpeakerStage`와 `ImitationJudgeStage` 간의 데이터 계약을 명확히 하여 구현 혼선을 방지한다.
*   **AC**:
    1.  **Schema Versioning**: `segment_schema_version`, `pair_schema_version` 필드 추가 (예: "1.0").
    2.  **Stable IDs & Units (Schema Separation)**:
        -   **SegmentSchema**: `segment_id` (UUID), `start_s`, `end_s`, `speaker_label`, `energy_db` (PCM Float [-1.0, 1.0] 기준 dBFS, 20*log10(RMS+eps)), `f0_median_hz`, `voiced_fraction`, `jitter_local_pct`, `shimmer_local_pct`, `hnr_db`, `quality_flags[]`
        -   **PairSchema**: `pair_id` (Trial+Rep+Index), `trial_index`, `rep_index`, `trial_start_s`, `trial_end_s`, `response_window_start_s`, `response_window_end_s`, `stimulus_id`, `stimulus_segment_id`, `stimulus_start_s`, `stimulus_end_s`, `response_segment_id`, `response_start_s`, `response_end_s`
        -   **Meta**: `audio_sr_hz` (16000), `feature_hop_ms` (10), `pitch_range_hz` (75~1000), `voicing_threshold` (0.45)
    3.  **Enums & Severity Mapping**:
        -   `speaker_label`: `ADULT`, `CHILD`, `UNKNOWN`
        -   **Severity Policy**:
            -   `FAIL`: `NO_SPEECH`, `NO_RESPONSE`, `NO_CHILD_CANDIDATE`, `INSUFFICIENT_STIMULUS`, `INSUFFICIENT_FEATURE_FRAMES`
            -   **Policy-Dependent**: `RESPONSE_NOT_CHILD` (Default: `WARN`, Strict: `FAIL`)
            -   `WARN`: `UNRELIABLE_VOICE_QUALITY`, `LOW_SNR`, `MULTI_SPEAKER`, `OVERLAP`, `LOW_HNR`, `LOW_VOICING`
            -   `PASS`: 정상 매칭
    4.  **Decision Trace**:
        -   **PairSchema**에 다음 필드를 추가한다: `candidate_segment_ids`, `candidate_pre_scores`, `chosen_reason`, `policy_mode` (`DEFAULT` vs `STRICT`), `severity_nominal`, `severity_effective`.
        -   **Alignment Rule**: Candidate List들은 인덱스별로 동일한 후보를 가리켜야 한다.
        -   `chosen_reason` Enum: `HIGHEST_SCORE`, `FALLBACK_UNKNOWN`, `NO_CANDIDATE`, `TIE_BREAKER_LONGEST`
    5.  **Nullable Rule**: Reliability Gate 미통과 시, 해당 지표는 `None`으로 통일한다.

#### **[AI-407A] BAD_PROSODY 게이트 제거 (Logic Fix)**
*   **User Story**: 현재 로직은 `F0 > 450Hz`일 때만 단조로움을 체크하므로, 저음의 "로봇 목소리"를 놓친다. 이는 모델 성능 문제가 아니라 명백한 로직 결함이므로 즉시 수정한다.
*   **AC**:
    1.  `BAD_PROSODY` 게이트 조건을 제거하고, `MONOTONE`(단조로움) 플래그는 F0 높낮이와 무관하게 항상 검사한다.
    2.  `SQUEAL`(고음/비명) 플래그와 `MONOTONE` 플래그를 분리하여 독립적으로 저장한다.
    3.  **Robustness**: MAD 계산 시 **Voiced Frame(Parselmouth 기준)**만 사용하며, F0 데이터에 **Median Filter**(`window=50ms`)를 적용하여 튀는 값을 방지한다.

#### **[AI-401A] Pitch Extraction 교체 (Tool Swap)**
*   **User Story**: 지연 시간이 너무 길어(50초) 서비스가 불가능하므로, 느린 `librosa.pyin`을 C++ 기반의 `Parselmouth`로 교체하여 속도를 확보한다. 로직 변경 없이 도구만 교체한다.
*   **AC**:
    1.  **Latency**: **VAD로 검출된 Speech Segment**에 대해 `Pitch + VoiceQuality` 단계의 처리 시간이 **p95 < 1.0s**(1분 오디오 기준)여야 한다. (Warm Start 조건)
    2.  **Voice Quality Extraction**: `Jitter`, `Shimmer`, `HNR` 지표가 추가로 추출되어야 한다. (AI-407B 지원)
    3.  **Parselmouth Reliability Gate**:
        -   **Common**: `duration >= 0.3s` AND `voiced_fraction >= min_voiced_ratio(0.6)`.
        -   **Metric-specific**: Jitter/Shimmer는 `num_periods >= 20` 또는 `voiced_frames >= 30` (hop=10ms 기준) 조건을 만족해야 한다.
        -   **Failure Handling**: Gate 미달 시 음질 지표를 `None`으로 처리하고 `VOICE_QUALITY_UNRELIABLE` 상태와 `WARN` Severity를 마킹한다.
*   **Tech Notes**:
    *   **Pitch Config**: 초기 추출 범위는 `75~1000Hz` (Wide Range)로 넓게 잡고, 이후 `f0_median` 기반으로 Adult/Child를 분류하는 후처리 방식이 안전하다. (엄격한 Range 분리는 옥타브 에러 위험 존재)

#### **[AI-407B] 정밀 음질 지표 플래그 추가 (Metric Expansion)**
*   **User Story**: AI-401A로 추출된 `Jitter`, `Shimmer`, `HNR` 값을 활용하여 세부적인 음질 이상(거친 소리, 기식음)을 탐지한다.
*   **AC**:
    1.  **`LOW_HNR` (거친 소리)**: HNR 값이 임계치(예: **초기 10dB**, Golden 재튜닝) 미만일 때 플래그 설정.
    2.  **`LOW_VOICING` (기식음)**: Voiced Fraction이 임계치(예: **초기 0.6**, Golden 재튜닝) 미만일 때 플래그 설정.
    3.  위 지표들은 `Reliability Gate`를 통과한 유효 구간에 대해서만 판정하며, 임계치는 `config.py`에서 관리한다.

---

### **Track 2: Realistic Refactoring (정확도 및 안정성 보강)**

#### **[AI-404] Protocol-based Matching 로직 구현**
*   **User Story**: "순서 끼워맞추기"로 인한 오판을 막기 위해, 엄마 발화 후 타임아웃 내 아기 발화를 검색하는 방식으로 변경한다.
*   **AC**:
    1.  **Scenario A (침묵)**: 아기가 침묵 시 `NO_RESPONSE`로 정확히 처리되어야 한다.
    2.  **Scenario B (잡음)**: 5초 윈도우 내에 잡음과 아기 목소리가 섞여 있어도 `Child` 라벨이 붙은 가장 신뢰도 높은 구간을 선택한다.
    3.  **Stimulus Mapping Rules (Fixed 8s Protocol)**:
        -   **Trial Definition**: 각 Trial은 `TRIAL_DURATION_SEC`(8.0s) 동안 진행되며, 전체 세션은 `Trial 1 (0~8s)`, `Trial 2 (8~16s)`... 와 같이 고정 슬롯으로 구성된다.
        -   `trial_start_s` = `Session Start` + `(Trial Index * 8.0)`. (고정 시간 슬롯 준수)
        -   **Prompt Constraint**: `trial_start_s` ~ `trial_start_s + 3.0s` 구간 내에 시작된(`onset`) 첫 번째 `ADULT` Segment를 `Stimulus`로 매핑한다.
        -   (Merging 로직 적용 후) 만약 3.0s 내에 유효한 ADULT 발화가 없으면 `INSUFFICIENT_STIMULUS` (FAIL) 처리한다.
    4.  **Candidate Selection Rules**:
        -   **Window Logic (Onset Base)**: 엄마 발화 시작 시점(`Stimulus Onset`)부터 5초간, 단 Trial 종료 시점(8초)을 넘지 않도록 설정한다.
            -   `window_start = stimulus_start_s`
            -   `window_end = min(stimulus_start_s + RESPONSE_TIMEOUT(5.0), trial_start_s + TRIAL_DURATION_SEC(8.0))`
            -   **Candidate Condition**:
                -   `seg.end_s > window_start` **AND** `seg.start_s >= window_start` (엄마 발화 시작 이후에 시작된 발화만 인정)
                -   엄마 발화와 겹치는 경우(`overlap`)는 별도 정책(`OVERLAP` Flag) 및 패널티를 적용한다.
        -   **Feature Clipping Policy (Overlap Protection)**:
            -   **DEFAULT (Strict)**: `clip_start = max(seg.start_s, stimulus_end_s)`. 엄마 목소리가 섞이는 것을 원천 차단한다. (반응 앞부분이 잘릴 수 있음)
            -   **LENIENT**: `clip_start = max(seg.start_s, window_start)`. 겹침 반응도 인정하되, Overlap Penalty를 강화한다.
            -   `clip_end = min(seg.end_s, window_end)`.
            -   잘린 구간의 길이가 너무 짧으면(예: < 0.2s) `INSUFFICIENT_FEATURE_FRAMES`로 처리한다.
        -   1차 필터 (**Top-K**):
            -   `voiced_fraction`이 `None`인 경우 `0.0`으로 처리하고 `UNRELIABLE_VOICE_QUALITY` Flag를 추가한다.
            -   `norm_energy = clip01((energy_db - p50_speech_db) / (p95_speech_db - p50_speech_db + eps))` (p50/p95는 Run-level 집계값 사용)
            -   `Pre-score = 0.6*voiced_fraction + 0.3*norm_energy + 0.1*clip01(duration_s / 2.0)`
            -   `speaker_label==CHILD`인 구간 중 Pre-score 상위 **K=3**개 선정.
            -   **Fallback**: CHILD가 0개면 `UNKNOWN` 중 Top-1을 선정하되, `RESPONSE_NOT_CHILD` (WARN/FAIL) 상태로 마킹.
        -   2차 랭킹: `Score = Similarity - λ*NoisePenalty - γ*OverlapPenalty + μ*DurationBonus`. (Overlap 구간에 Penalty 부여)
    5.  **Failure Taxonomy (Order Priority)**:
        1.  `NO_RESPONSE`: 매칭 윈도우 내 어떠한 Speech Segment도 없음 (Speech Count = 0)
        2.  `NO_CHILD_CANDIDATE`: Speech는 있으나 (CHILD + UNKNOWN) 후보가 없음 (Only ADULT exists)
        3.  `LOW_SNR`: Proxy SNR 비율이 `LOW_SNR_DB_TH`(10dB) 미만.
        4.  `MULTI_SPEAKER`: 화자 라벨 스위칭(`label_flip_count` > 4) 과다 (범위: Stimulus End ~ Window End)
    6.  **Meta**: `audio_sr_hz` (16000), `feature_hop_ms` (10), `pitch_floor_hz` (75), `pitch_ceil_hz` (1000)

#### **[AI-401B] 화자 분리 보강 (Dynamic Thresholding)**
*   **User Story**: AI-401A로 속도가 확보된 상태에서, 단순 200Hz 룰 대신 **동적 임계값(Clustering)**을 적용하여 화자 분리 정확도를 높인다.
*   **AC**:
    1.  **Input Robustness**: F0 추출 시 `Median` 또는 `Trimmed Mean`을 사용하여 옥타브 오류 영향을 줄인다. 클러스터링은 프레임 단위가 아닌 **세그먼트 단위**로 수행한다.
    2.  **Unimodal Check**: Pitch 분포가 단봉(Cluster 간 거리 < 3 semitones)인 경우 클러스터링을 포기하고 Fallback(기본 룰)을 따른다.
    3.  Voicing Ratio가 낮은 구간(잡음/무성음)은 클러스터링 입력에서 제외한다.

#### **[AI-403] Silero VAD ONNX 전환 & 의존성 고정**
*   **User Story**: `torch.hub.load`는 인터넷 의존성이 있고 느리므로, ONNX 모델을 로컬에 포함하여 배포 안정성을 높인다.
*   **AC**:
    1.  인터넷 차단 환경에서도 VAD가 동작해야 한다. (Local Model)
    2.  ONNX Runtime 사용 시 추론 속도가 PyTorch 대비 개선되어야 한다.

#### **[AI-402] DTW_Band (DTW_RADIUS) 튜닝 & Golden 검증**
*   **User Story**: 현재 `Band` 제한이 없거나 느슨하여(Full Search) 속도가 느릴 수 있다. `DTW_BAND_SEC`를 적절히 좁혀(0.3~0.5초) 속도를 높이고 정확도를 유지한다.
*   **AC**:
    1.  `config.py`에 `DTW_BAND_SEC` 및 `FEATURE_HOP_MS`(기본 10ms)를 정의한다.
    2.  코드 내에서 `radius_frames = round(DTW_BAND_SEC * 1000 / FEATURE_HOP_MS)` 로 변환하되, **최소 3프레임(30ms), 최대 min(len_x, len_y)-1**로 Clamp하여 안전성을 확보한다.
    3.  Band 적용 시 `radius_frames < abs(len_x - len_y)`인 경우, 경로 생성 불가(Impossible Path)를 방지하기 위해 `radius_frames = max(radius_frames, abs(len_x - len_y))` 보정을 수행한다.
    4.  Band 적용 시 유사도 계산 시간이 50% 이상 단축됨을 확인한다.

#### **[AI-408] Response 화자 일관성 체크 강화 (Policy Enforcement)**
*   **User Story**: AI-404에서 선택된 구간(`CHILD` or `UNKNOWN`)이 실제 `CHILD` 화자인지 재검증하여, 정책에 따라 경고(WARN) 또는 실패(FAIL) 처리한다.
*   **AC**:
    1.  **Strict Mode**: `speaker_label != CHILD`이면 `severity=FAIL`로 처리하고 매칭 실패시킴.
    2.  **Default Mode**: `speaker_label != CHILD` (UNKNOWN Fallback)이면 `severity=WARN`으로 유지하고, `chosen_reason=FALLBACK_UNKNOWN`을 기록한다.
    3.  엄마 목소리가 아기 목소리로 오분류된 경우를 방어하기 위해, `Parselmouth` 피처(Formant 등)를 보조 지표로 활용할 수 있는지 검토한다(Optional).
