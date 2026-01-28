# services/name_non_facing/app/pipeline/stages/trigger_stage.py
"""
호명 트리거 감지 Stage

부모의 호명(아이 이름 부르기)을 감지하고 T_start를 기록합니다.

설계 의도:
    1. 트리거 정의
       - 호명 종료 시점(T_start) = 반응 측정 시작점
       - 이 시점부터 timeout_sec 동안 반응 감지
       
    2. 호명 패턴 인식
    # TODO : 고도화 필요.
       - 한국어 호격 조사: "{이름}아", "{이름}야"
       - 애칭 패턴: "우리 {이름}", "{이름}이"
       - 명령형: "{이름}아, 여기 봐"

Reference:
    - 한국어 호격 조사: https://ko.wikipedia.org/wiki/조사_(품사)
    - Whisper word timestamps: https://github.com/openai/whisper#word-level-timestamps
"""

from typing import Optional
import logging

from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.context import PipelineContext
from app.models.speech_recognizer import SpeechRecognizer
from app.config import get_settings

logger = logging.getLogger(__name__)


class TriggerStage(BaseStage):
    """
    호명 트리거 감지 Stage
    
    전체 오디오를 음성 인식하고, 호명 이벤트를 탐지합니다.
    
    Input:
        - context.audio: 오디오 데이터
        - context.sample_rate: 샘플레이트
        - context.child_name: 아이 이름
        
    Output:
        - context.transcription: 전체 음성 인식 결과
        - context.name_call_events: 호명 이벤트 목록 (T_start 포함)
    """
    
    def __init__(self, recognizer: SpeechRecognizer = None):
        """
        Args:
            recognizer: 음성 인식기 (None이면 자동 생성)
                       - DI(Dependency Injection)로 테스트 용이성 확보
        """
        self._settings = get_settings()
        self._recognizer = recognizer or SpeechRecognizer()
    
    @property
    def name(self) -> str:
        return "TriggerStage"
    
    def validate(self, context: PipelineContext) -> Optional[str]:
        """오디오 데이터 존재 여부 검증"""
        if context.audio is None:
            return "오디오 데이터가 없습니다. InputStage를 먼저 실행하세요."
        if not context.child_name:
            return "아이 이름이 설정되지 않았습니다."
        return None
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        호명 이벤트 탐지
        
        Process:
            1. 전체 오디오 음성 인식 (faster-whisper)
            2. 호명 패턴 매칭 (정규식 기반)
            3. 호명 이벤트 목록 생성 (시간순)
        """
        # 1. 전체 오디오 음성 인식
        logger.info(f"🩵 음성 인식 시작 (아이 이름: {context.child_name})")
        
        transcription = self._recognizer.transcribe(
            audio=context.audio,
            sample_rate=context.sample_rate
        )
        context.transcription = transcription
        
        logger.info(
            f"🩵 음성 인식 완료: "
            f"언어={transcription.language} "
            f"({transcription.language_probability:.1%}), "
            f"텍스트='{transcription.text[:50]}...'" 
            if len(transcription.text) > 50 
            else f"텍스트='{transcription.text}'"
        )
        
        # 2. 호명 이벤트 탐지
        name_calls = self._recognizer.find_name_calls(
            transcription=transcription,
            child_name=context.child_name
        )
        context.name_call_events = name_calls
        
        # 3. 결과 로깅
        if name_calls:
            logger.info(f"🩵🩵🩵 호명 감지: {len(name_calls)}회")
            for i, call in enumerate(name_calls, 1):
                logger.info(
                    f"  [{i}] '{call.text}' @ "
                    f"{call.start_sec:.2f}s ~ {call.end_sec:.2f}s "
                    f"(T_start = {call.end_sec:.2f}s)"
                )
        else:
            context.add_warning(
                self.name, 
                "호명 이벤트가 감지되지 않았습니다"
            )
            logger.warning("✖️✖️✖️ 호명이 감지되지 않았습니다")
        
        return context
