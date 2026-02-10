# 디렉토리 구조..
```
├── pipeline/                            # 분석 파이프라인
    ├── __init__.py
    ├── orchestrator.py                  # 파이프라인 오케스트레이터
    ├── stages/
    │   ├── __init__.py
    │   ├── base_stage.py                # BaseStage 추상 클래스
    │   ├── input_stage.py               # 입력 처리 (영상/음성 분리)
    │   ├── face_detect_stage.py         # 얼굴 탐지 & 위치 벡터
    │   ├── trigger_stage.py             # 호명 트리거 탐지
    │   ├── child_analysis_stage.py      # 아이 분석 :  Vision + Audio 통합
    │   ├── reaction_detect_stage.py     # 복합 반응 판정
    │   └── result_stage.py              # 결과 집계
    └── context.py                       # 파이프라인 컨텍스트
```

전체 파이프라인 흐름
```
┌─────────────────────────────────────────────────────────────┐
│                    PipelineOrchestrator                     │
│  (파이프라인 실행 제어, Stage 순차 실행, 에러 처리)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     PipelineContext                         │
│  (파이프라인 상태 공유, 중간 결과 저장, 메타데이터)             │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Stage 1 │    →     │ Stage 2 │    →     │ Stage N │
   └─────────┘          └─────────┘          └─────────┘
```

# stage 정의
| Stage                   | 파일                       | 입력                    | 출력                  | 사용 모델          |
| ----------------------- | -------------------------- | ----------------------- | --------------------- | ------------------ |
| **InputStage**          | `input_stage.py`           | video_path              | audio, frames         | FFmpeg             |
| **TriggerStage**        | `trigger_stage.py`         | audio, child_name       | name_calls (T_start)  | SpeechRecognizer   |
| **FaceDetectStage**     | `face_detect_stage.py`     | frames                  | parent_pos, child_pos | FaceDetector       |
| **ReactionDetectStage** | `reaction_detect_stage.py` | audio, name_calls       | voice_reactions       | ChildVoiceAnalyzer |
| **ChildAnalysisStage**  | `child_analysis_stage.py`  | frames, voice_reactions | gaze_vectors          | HeadPose           |
| **ResultStage**         | `result_stage.py`          | all results             | final_metrics         | -                  |


### 전체 데이터 흐름

```
video_path (str)
    │
    ▼ InputStage
┌─────────────────────────────────────────────────────────┐
│ FFmpeg 오디오 추출                                       │
│ - 16kHz mono WAV 변환                                   │
│ - torchaudio 로드                                       │
└─────────────────────────────────────────────────────────┘
    │
    │ context.audio (np.ndarray)
    │ context.sample_rate (16000)
    │ context.audio_duration_sec (float)
    ▼ TriggerStage
┌─────────────────────────────────────────────────────────┐
│ faster-whisper 음성 인식                                 │
│ - 전체 오디오 → 텍스트                                     │
│ - 호명 패턴 매칭 ("{이름}아", "{이름}야" 등)                 │
└─────────────────────────────────────────────────────────┘
    │
    │ context.transcription (TranscriptionResult)
    │ context.name_call_events (List[NameCallEvent])
    │   └── text, start_sec, end_sec (T_start)
    ▼ ReactionDetectStage
┌─────────────────────────────────────────────────────────┐
│ pyannote-audio 화자 분리                                 │
│ - 부모/아이 화자 구분                                     │
│                                                         │
│ ChildVoiceAnalyzer 반응 분석                              │
│ - T_start 이후 음성 활동 탐지 (VAD)                        │
│ - 아이 화자 구간과 매칭                                    │
│ - Latency 계산                                           │
└─────────────────────────────────────────────────────────┘
    │
    │ context.diarization (DiarizationResult)
    │ context.voice_reactions (List[ChildVoiceReaction])
    │   └── detected, start_sec, latency_sec, duration_sec
    ▼ ResultStage
┌─────────────────────────────────────────────────────────┐
│ 시도별 결과 통합                                           │
│ - 음성 반응 OR 시선 반응 → 성공                             │
│ - Latency 결정 (음성 우선)                                 │
│ - TrialResult 생성                                       │
└─────────────────────────────────────────────────────────┘
    │
    │ context.trial_results (List[TrialResult])
    ▼
┌─────────────────────────────────────────────────────────┐
│ 최종 JSON 결과                                           │
│ {                                                       │
│   "request_id": "uuid",                                 │
│   "status": "completed",                                │
│   "metrics": { "per_trial": [...] }                     │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

### 최종 응답 형식

```json
{
  "request_id": "uuid",
  "analyzed_at": "2026-01-28T18:00:00+09:00",
  "metrics": {
    "per_trial": [
      {
        "trial_index": 1,
        "success": true,
        "latency_s": 0.54,
        "voice_detected": true,
        "voice_duration_s": 0.45,
        "gaze_match": true,
        "gaze_duration_s": 1.20,
        "head_yaw_deg": 15.5,
        "head_pitch_deg": 5.2
      },
      {
        "trial_index": 2,
        "success": false,
        "latency_s": null,
        "voice_detected": false,
        "gaze_match": false
      }
    ]
  },
  "processing_times": {
    "InputStage": 0.5,
    "TriggerStage": 12.3,
    "ReactionDetectStage": 1.8,
    "ResultStage": 0.1
  }
}
```

## 클래스 다이어그램
```
┌───────────────────────────────────────────┐
│          AudioPipelineOrchestrator        │
├───────────────────────────────────────────┤
│ - stages: List[BaseStage]                 │
├───────────────────────────────────────────┤
│ + run(video_path, child_name) → Dict      │
│ + run_with_context(context) → Context     │
└───────────────────────────────────────────┘
                    │
                    │ uses
                    ▼
┌───────────────────────────────────────────┐
│              PipelineContext              │
├───────────────────────────────────────────┤
│ + request_id: str                         │
│ + video_path: str                         │
│ + child_name: str                         │
│ + audio: np.ndarray                       │
│ + name_call_events: List[NameCallEvent]   │
│ + voice_reactions: List[ChildVoiceReaction]│
│ + trial_results: List[TrialResult]        │
├───────────────────────────────────────────┤
│ + to_result() → Dict                      │
└───────────────────────────────────────────┘
                    ▲
                    │ modifies
                    │
┌───────────────────────────────────────────┐
│            BaseStage (Abstract)           │
├───────────────────────────────────────────┤
│ + name: str (abstract)                    │
├───────────────────────────────────────────┤
│ + run(context) → Context                  │
│ + process(context) → Context (abstract)   │
│ + validate(context) → Optional[str]       │
└───────────────────────────────────────────┘
          △         △         △         △
          │         │         │         │
   ┌──────┘   ┌─────┘   ┌─────┘   ┌─────┘
   │          │         │         │
┌─────┐  ┌─────────┐ ┌───────────┐ ┌────────┐
│Input│  │Trigger  │ │Reaction   │ │Result  │
│Stage│  │Stage    │ │DetectStage│ │Stage   │
└─────┘  └─────────┘ └───────────┘ └────────┘
```