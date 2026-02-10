# services/name_non_facing/app/pipeline/stages/reaction_detect_stage.py
"""
음성 반응 감지 Stage

호명 이후 아이의 음성 반응을 감지합니다.

설계 의도:
    1. 반응 시간 측정 (Latency)
       - T_start (호명 종료) ~ T_react (반응 시작) 간격
       
    2. 화자 기반 필터링
       - 화자 분리로 부모/아이 구분
       - 아이 발화만 반응으로 인정
       
    3. Fallback 전략
       - 화자 분리 실패 시 VAD 기반 판단
       - 호명 직후 첫 발화 = 아이 반응 가정

처리 과정:
    1. 화자 분리 (전체 오디오에 대해 1회)
        └── pyannote-audio speaker-diarization-3.1
        └── 부모/아이 화자 식별

    2. 각 호명(Trial)에 대해:
        ├── T_start (호명 종료) ~ T_start + timeout 구간 추출
        ├── VAD로 음성 활동 탐지
        ├── 화자 분리 결과와 매칭 (아이 발화 필터링)
        └── Latency = 첫 아이 발화 시작 - T_start

"""

from typing import Optional
import logging

from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.context import PipelineContext
from app.models.child_voice_analyzer import ChildVoiceAnalyzer
from app.models.speaker_diarizer import SpeakerDiarizer
from app.config import get_settings

logger = logging.getLogger(__name__)


class ReactionDetectStage(BaseStage):
    """
    음성 반응 감지 Stage
    
    각 호명 이벤트에 대해 아이의 음성 반응을 분석합니다.
    
    Input:
        - context.audio: 오디오 데이터
        - context.sample_rate: 샘플레이트
        - context.name_call_events: 호명 이벤트 목록
        
    Output:
        - context.diarization: 화자 분리 결과
        - context.voice_reactions: 음성 반응 목록
    """
    
    def __init__(
        self,
        analyzer: ChildVoiceAnalyzer = None,
        diarizer: SpeakerDiarizer = None
    ):
        """
        Args:
            analyzer: 아이 음성 분석기 (None이면 자동 생성)
            diarizer: 화자 분리기 (None이면 자동 생성)
        """
        self._settings = get_settings()
        self._diarizer = diarizer or SpeakerDiarizer()
        self._analyzer = analyzer or ChildVoiceAnalyzer(diarizer=self._diarizer)
    
    @property
    def name(self) -> str:
        return "ReactionDetectStage"
    
    def validate(self, context: PipelineContext) -> Optional[str]:
        """오디오 데이터 존재 여부 검증"""
        if context.audio is None:
            return "오디오 데이터가 없습니다."
        return None
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        음성 반응 감지
        
        Process:
            1. 화자 분리 수행 (한 번만)
            2. 각 호명에 대해 반응 분석
            3. Latency 및 Duration 계산
        """
        # 호명이 없으면 건너뛰기
        if not context.name_call_events:
            logger.info("✖️✖️✖️ 호명 이벤트 없음, 반응 감지 생략")
            return context
        
        # 1. 화자 분리 수행 (전체 오디오에 대해 한 번만)
        logger.info("🩵 화자 분리 시작...")
        
        # 첫 번째 호명 시점을 힌트로 제공 (호명자 = 부모)
        first_call_time = context.name_call_events[0].end_sec
        
        diarization = self._diarizer.diarize(
            audio=context.audio,
            sample_rate=context.sample_rate,
            name_call_time=first_call_time
        )
        context.diarization = diarization
        
        logger.info(
            f"🩵 화자 분리 완료: "
            f"{diarization.num_speakers}명 화자, "
            f"{len(diarization.segments)}개 구간"
        )
        
        # 2. 각 호명에 대해 반응 분석
        logger.info(f"🩵 {len(context.name_call_events)}개 호명에 대한 반응 분석...")
        
        reactions = self._analyzer.analyze_all_trials(
            audio=context.audio,
            sample_rate=context.sample_rate,
            name_call_events=context.name_call_events,
            diarization=diarization,
            timeout_sec=self._settings.REACTION_TIMEOUT_SEC
        )
        context.voice_reactions = reactions
        
        # 3. 결과 로깅
        for i, (call, reaction) in enumerate(
            zip(context.name_call_events, reactions), 1
        ):
            if reaction.detected:
                logger.info(
                    f"  [시도 {i}] 🩵🩵🩵 반응 감지! "
                    f"Latency: {reaction.latency_sec:.2f}s, "
                    f"Duration: {reaction.duration_sec:.2f}s"
                )
            else:
                logger.info(f"  [시도 {i}] ✖️✖️✖️ 반응 없음")
        
        return context
