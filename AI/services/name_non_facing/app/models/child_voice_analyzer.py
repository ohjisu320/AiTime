# services/name_non_facing/app/models/child_voice_analyzer.py
"""
아이 음성 반응 분석기

VAD, 화자 분리, 음성 인식을 통합하여
호명에 대한 아이의 음성 반응을 분석합니다.

통합 분석기 필요성:
    - 각 모델(VAD, Diarization, STT)은 독립적으로 동작하지만, "호명 반응 분석"이라는 목적을 위해 결과를 조합하는 상위 모듈이 필요합니다.

분석 흐름:
    1. VAD: 반응 대기 구간 내 음성 활동 탐지
    2. Diarization: 아이 발화 구간 필터링
    3. STT: 발화 내용 인식 (선택)

```
호명 종료 시점 (T_start)
    │
    ▼
┌─────────────────────────────────────────┐
│  1. VAD: 반응 대기 구간 내 음성 활동 탐지   │
│     → 음성 구간 후보 추출                 │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  2. Diarization: 아이 발화 구간 필터링     │
│     → 아이 화자 ID와 매칭                 │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  3. STT: 발화 내용 인식 (선택)            │
│     → 텍스트 변환                        │
└─────────────────────────────────────────┘
    │
    ▼
ChildVoiceReaction 결과
```
"""

from dataclasses import dataclass
from typing import List, Optional
import logging

import numpy as np

from app.config import get_settings
from app.models.vad import VoiceActivityDetector, SpeechSegment
from app.models.speaker_diarizer import (
    SpeakerDiarizer, 
    DiarizationResult, 
    SpeakerLabel
)
from app.models.speech_recognizer import SpeechRecognizer, NameCallEvent

logger = logging.getLogger(__name__)


@dataclass
class ChildVoiceReaction:
    """아이 음성 반응 결과"""
    detected: bool                      # 반응 감지 여부
    start_sec: Optional[float] = None   # 발화 시작 시점 (절대 시간)
    end_sec: Optional[float] = None     # 발화 종료 시점
    duration_sec: Optional[float] = None  # 발화 지속 시간
    latency_sec: Optional[float] = None   # T_start 대비 반응 지연
    confidence: float = 0.0             # 감지 신뢰도
    transcription: Optional[str] = None # 발화 내용 (선택)
    
    @classmethod
    def not_detected(cls) -> "ChildVoiceReaction":
        """반응 없음 결과 생성"""
        return cls(detected=False)
    
    def __repr__(self) -> str:
        if self.detected:
            return (
                f"ChildVoiceReaction(detected=True, "
                f"latency={self.latency_sec:.2f}s, "
                f"duration={self.duration_sec:.2f}s)"
            )
        return "ChildVoiceReaction(detected=False)"


class ChildVoiceAnalyzer:
    """
    아이 음성 반응 통합 분석기
    
    호명 종료 시점(T_start) 이후, 반응 대기 시간 내에
    아이의 음성 반응이 있는지 분석합니다.
    
    Usage:
        analyzer = ChildVoiceAnalyzer()
        
        # 사전에 화자 분리 결과 필요
        diarization = diarizer.diarize(audio, sample_rate)
        
        # 호명 종료 후 아이 음성 반응 분석
        reaction = analyzer.analyze(
            audio=audio,
            sample_rate=16000,
            trigger_end_sec=5.0,    # 호명 종료 시점
            timeout_sec=5.0,        # 반응 대기 시간
            diarization=diarization
        )
        
        if reaction.detected:
            print(f"반응 감지! Latency: {reaction.latency_sec:.2f}s")
    """
    
    def __init__(
        self,
        vad: VoiceActivityDetector = None,
        diarizer: SpeakerDiarizer = None,
        recognizer: SpeechRecognizer = None,
        transcribe_response: bool = False
    ):
        """
        Args:
            vad: VAD 인스턴스 (None이면 자동 생성)
            diarizer: 화자 분리기 (None이면 자동 생성)
            recognizer: 음성 인식기 (None이면 자동 생성)
            transcribe_response: 발화 내용을 텍스트로 변환할지 여부
        """
        self._settings = get_settings()
        
        self._vad = vad or VoiceActivityDetector()
        self._diarizer = diarizer or SpeakerDiarizer()
        self._recognizer = recognizer if transcribe_response else None
        self._transcribe_response = transcribe_response
        
        logger.info("😸 ChildVoiceAnalyzer 초기화 완료")
    
    def analyze(
        self,
        audio: np.ndarray,
        sample_rate: int,
        trigger_end_sec: float,
        timeout_sec: float = None,
        diarization: DiarizationResult = None
    ) -> ChildVoiceReaction:
        """
        아이 음성 반응 분석
        
        Args:
            audio: 전체 오디오 데이터
            sample_rate: 샘플레이트
            trigger_end_sec: 호명 종료 시점 (T_start)
            timeout_sec: 반응 대기 시간 (기본값: 설정값)
            diarization: 사전 화자 분리 결과 (없으면 자동 수행)
            
        Returns:
            ChildVoiceReaction: 아이 음성 반응 결과
        """
        if timeout_sec is None:
            timeout_sec = self._settings.REACTION_TIMEOUT_SEC
        
        analysis_end_sec = trigger_end_sec + timeout_sec
        
        # 오디오 길이 확인
        audio_duration = len(audio) / sample_rate
        if trigger_end_sec >= audio_duration:
            logger.warning(
                f"호명종료시점({trigger_end_sec:.2f}s)이 "
                f"오디오 길이({audio_duration:.2f}s)를 초과"
            )
            return ChildVoiceReaction.not_detected()
        
        analysis_end_sec = min(analysis_end_sec, audio_duration)
        
        # Step 1: 분석 구간 내 음성 활동 탐지 (VAD)
        speech_segments = self._vad.detect_in_range(
            audio=audio,
            start_sec=trigger_end_sec,
            end_sec=analysis_end_sec,
            sample_rate=sample_rate
        )
        
        if not speech_segments:
            logger.debug(
                f"반응 구간 ({trigger_end_sec:.2f}s ~ {analysis_end_sec:.2f}s) "
                f"내 음성 활동 없음"
            )
            return ChildVoiceReaction.not_detected()
        
        # Step 2: 화자 분리 결과에서 아이 발화 필터링
        if diarization is None:
            logger.debug("화자 분리 수행...")
            diarization = self._diarizer.diarize(audio, sample_rate)
        
        child_reaction = self._find_child_response(
            speech_segments=speech_segments,
            diarization=diarization,
            trigger_end_sec=trigger_end_sec,
            analysis_end_sec=analysis_end_sec
        )
        
        if child_reaction is None:
            logger.debug("아이 발화로 식별된 음성 없음")
            return ChildVoiceReaction.not_detected()
        
        # Step 3: (선택) 발화 내용 인식
        if self._transcribe_response and self._recognizer:
            transcription = self._transcribe_child_response(
                audio=audio,
                sample_rate=sample_rate,
                start_sec=child_reaction.start_sec,
                end_sec=child_reaction.end_sec
            )
            child_reaction.transcription = transcription
        
        logger.info(
            f"아이 음성 반응 감지: "
            f"{child_reaction.start_sec:.2f}s ~ {child_reaction.end_sec:.2f}s, "
            f"Latency: {child_reaction.latency_sec:.2f}s"
        )
        
        return child_reaction
    
    def _find_child_response(
        self,
        speech_segments: List[SpeechSegment],
        diarization: DiarizationResult,
        trigger_end_sec: float,
        analysis_end_sec: float
    ) -> Optional[ChildVoiceReaction]:
        """
        VAD 구간과 화자 분리 결과를 매칭하여 아이 발화 찾기
        
        매칭 전략:
        1. VAD 구간과 Diarization 구간의 겹침 확인
        2. 겹치는 구간 중 아이(CHILD) 라벨인 구간 선택
        3. 가장 빠른 반응 반환
        """
        # 분석 범위 내 아이 발화 구간
        child_diar_segments = diarization.get_segments_in_range(
            start_sec=trigger_end_sec,
            end_sec=analysis_end_sec,
            label=SpeakerLabel.CHILD
        )
        
        if not child_diar_segments:
            # 화자 분리에서 아이 발화를 찾지 못한 경우
            # VAD 결과만으로 판단 (첫 번째 음성 = 아이로 가정)
            # fallback
            # TODO: 향후 화자 분리 모델 개선 필요
            logger.debug("화자 분리에서 아이 발화 미탐지, VAD 기반 판단")
            return self._fallback_by_vad(speech_segments, trigger_end_sec)
        
        # VAD 구간과 Diarization 구간 매칭
        for vad_seg in sorted(speech_segments, key=lambda s: s.start_sec):
            for diar_seg in child_diar_segments:
                # 겹침 확인
                overlap_start = max(vad_seg.start_sec, diar_seg.start_sec)
                overlap_end = min(vad_seg.end_sec, diar_seg.end_sec)
                
                if overlap_start < overlap_end:
                    # 겹치는 구간 발견 → 아이 반응
                    return ChildVoiceReaction(
                        detected=True,
                        start_sec=overlap_start,
                        end_sec=overlap_end,
                        duration_sec=overlap_end - overlap_start,
                        latency_sec=overlap_start - trigger_end_sec,
                        confidence=vad_seg.confidence
                    )
        
        return None
    
    def _fallback_by_vad(
        self,
        speech_segments: List[SpeechSegment],
        trigger_end_sec: float
    ) -> Optional[ChildVoiceReaction]:
        """
        화자 분리 실패 시 VAD 기반 fallback
        
        가정: 호명 직후 첫 음성은 아이 반응일 가능성 높음
        (부모는 방금 호명을 끝냈으므로)
        """
        if not speech_segments:
            return None
        
        # 최소 발화 시간 필터링
        min_duration = self._settings.MIN_VOICE_DURATION_SEC
        
        for seg in sorted(speech_segments, key=lambda s: s.start_sec):
            if seg.duration_sec >= min_duration:
                return ChildVoiceReaction(
                    detected=True,
                    start_sec=seg.start_sec,
                    end_sec=seg.end_sec,
                    duration_sec=seg.duration_sec,
                    latency_sec=seg.start_sec - trigger_end_sec,
                    confidence=seg.confidence * 0.7  # fallback이므로 신뢰도 감소
                )
        
        return None
    
    def _transcribe_child_response(
        self,
        audio: np.ndarray,
        sample_rate: int,
        start_sec: float,
        end_sec: float
    ) -> Optional[str]:
        """아이 발화 구간 텍스트 변환"""
        try:
            result = self._recognizer.transcribe_segment(
                audio=audio,
                start_sec=start_sec,
                end_sec=end_sec,
                sample_rate=sample_rate
            )
            return result.text.strip() if result.text else None
        except Exception as e:
            logger.warning(f"발화 내용 인식 실패: {e}")
            return None
    
    def analyze_all_trials(
        self,
        audio: np.ndarray,
        sample_rate: int,
        name_call_events: List[NameCallEvent],
        diarization: DiarizationResult = None,
        timeout_sec: float = None
    ) -> List[ChildVoiceReaction]:
        """
        모든 시도(Trial)에 대한 음성 반응 분석
        
        Args:
            audio: 전체 오디오
            sample_rate: 샘플레이트
            name_call_events: 호명 이벤트 목록
            diarization: 화자 분리 결과
            timeout_sec: 반응 대기 시간
            
        Returns:
            List[ChildVoiceReaction]: 시도별 반응 결과
        """
        if diarization is None:
            diarization = self._diarizer.diarize(audio, sample_rate)
        
        reactions = []
        
        for event in name_call_events:
            reaction = self.analyze(
                audio=audio,
                sample_rate=sample_rate,
                trigger_end_sec=event.end_sec,
                timeout_sec=timeout_sec,
                diarization=diarization
            )
            reactions.append(reaction)
        
        return reactions