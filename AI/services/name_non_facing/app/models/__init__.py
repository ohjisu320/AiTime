# services/name_non_facing/app/models/__init__.py
"""
AI 모델 래퍼 모듈

Audio Pipeline:
    - VoiceActivityDetector: Silero VAD 기반 음성 활동 탐지
    - SpeakerDiarizer: pyannote-audio 기반 화자 분리
    - SpeechRecognizer: faster-whisper 기반 음성 인식
    - ChildVoiceAnalyzer: 아이 음성 반응 통합 분석
"""

from app.models.base import BaseModel
from app.models.vad import VoiceActivityDetector, SpeechSegment
from app.models.speaker_diarizer import (
    SpeakerDiarizer,
    SpeakerLabel,
    SpeakerSegment,
    DiarizationResult
)
from app.models.speech_recognizer import (
    SpeechRecognizer,
    Word,
    Segment,
    TranscriptionResult,
    NameCallEvent
)
from app.models.child_voice_analyzer import (
    ChildVoiceAnalyzer,
    ChildVoiceReaction
)

__all__ = [
    # Base
    "BaseModel",
    # VAD
    "VoiceActivityDetector",
    "SpeechSegment",
    # Speaker Diarization
    "SpeakerDiarizer",
    "SpeakerLabel",
    "SpeakerSegment",
    "DiarizationResult",
    # Speech Recognition
    "SpeechRecognizer",
    "Word",
    "Segment",
    "TranscriptionResult",
    "NameCallEvent",
    # Child Voice Analysis
    "ChildVoiceAnalyzer",
    "ChildVoiceReaction",
]