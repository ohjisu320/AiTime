# services/name_non_facing/app/pipeline/stages/result_stage.py
"""
결과 산출 Stage

각 시도(Trial)별 결과를 종합하여 최종 메트릭을 생성합니다.

설계 의도:
    1. OR 로직 통합
       - 음성 반응 OR 시선 반응 → 성공
       - 어느 한쪽이라도 감지되면 반응 있음
       
    2. 확장 가능한 결과 구조
       - Vision 결과 추가 시 기존 코드 수정 최소화
       - TrialResult 데이터클래스로 타입 안전성 확보
       
    3. 표준 출력 형식
       - 필수참고_작업설계.md의 JSON 양식 준수

Reference:
    - 반응 판정 모드: config.py의 ReactionMode
    - 출력 양식: 필수참고_작업설계.md
"""

import logging

from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.context import PipelineContext, TrialResult
from app.config import get_settings, ReactionMode

logger = logging.getLogger(__name__)


class ResultStage(BaseStage):
    """
    결과 산출 Stage
    
    음성 반응과 (향후) 시선 반응을 통합하여 최종 결과를 생성합니다.
    
    Input:
        - context.name_call_events: 호명 이벤트 목록
        - context.voice_reactions: 음성 반응 목록
        - context.gaze_results: 시선 반응 목록 (향후)
        
    Output:
        - context.trial_results: 시도별 최종 결과
    """
    
    def __init__(self):
        self._settings = get_settings()
    
    @property
    def name(self) -> str:
        return "ResultStage"
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        최종 결과 산출
        
        Process:
            1. 각 시도(Trial)별 결과 생성
            2. 음성/시선 반응 통합 (OR/AND 로직)
            3. 성공 여부 및 Latency 결정
        """
        trial_results = []
        reaction_mode = self._settings.REACTION_MODE
        
        for i, name_call in enumerate(context.name_call_events):
            # 음성 반응 결과 (있으면)
            voice_reaction = (
                context.voice_reactions[i]
                if i < len(context.voice_reactions)
                else None
            )
            
            # 시선 반응 결과 (향후 Vision Stage에서 채움)
            gaze_result = (
                context.gaze_results[i]
                if i < len(context.gaze_results)
                else None
            )
            
            # 반응 여부 판정
            voice_detected = (
                voice_reaction is not None and 
                voice_reaction.detected
            )

            gaze_match = (
                gaze_result is not None and 
                getattr(gaze_result, 'match', False)
            )
            
            # 성공 여부 판정 (ReactionMode에 따라)
            success = self._determine_success(
                voice_detected=voice_detected,
                gaze_match=gaze_match,
                mode=reaction_mode
            )
            
            # Latency 결정 (음성 반응 우선, 없으면 시선 반응)
            latency = None
            if voice_detected and voice_reaction.latency_sec is not None:
                latency = voice_reaction.latency_sec
            elif gaze_match and gaze_result is not None:
                latency = getattr(gaze_result, 'latency_sec', None)
            
            # TrialResult 생성
            trial_result = TrialResult(
                trial_index=i + 1,
                success=success,
                latency_s=latency,
                voice_detected=voice_detected,
                voice_start_s=(
                    voice_reaction.start_sec 
                    if voice_detected else None
                ),
                voice_end_s=(
                    voice_reaction.end_sec 
                    if voice_detected else None
                ),
                voice_duration_s=(
                    voice_reaction.duration_sec 
                    if voice_detected else None
                ),
                voice_confidence=(
                    voice_reaction.confidence 
                    if voice_detected else 0.0
                ),
                gaze_match=gaze_match,
                gaze_duration_s=(
                    getattr(gaze_result, 'duration_sec', None) 
                    if gaze_match else None
                ),
                head_yaw_deg=(
                    getattr(gaze_result, 'yaw_deg', None) 
                    if gaze_match else None
                ),
                head_pitch_deg=(
                    getattr(gaze_result, 'pitch_deg', None) 
                    if gaze_match else None
                ),
            )
            trial_results.append(trial_result)
        
        context.trial_results = trial_results
        
        # 결과 요약 로깅
        success_count = sum(1 for tr in trial_results if tr.success)
        total_count = len(trial_results)
        
        logger.info(
            f"🩷🩷🩷 결과 산출 완료: "
            f"{success_count}/{total_count} 시도 성공 "
            f"(모드: {reaction_mode.value})"
        )
        
        for tr in trial_results:
            status = "🩷" if tr.success else "✖️✖️✖️"
            latency_str = f"{tr.latency_s:.2f}s" if tr.latency_s is not None else "N/A"
            logger.info(
                f"  [시도 {tr.trial_index}] {status} "
                f"Latency: {latency_str}, "
                f"Voice: {tr.voice_detected}, Gaze: {tr.gaze_match}"
            )
        
        return context
    
    def _determine_success(
        self,
        voice_detected: bool,
        gaze_match: bool,
        mode: ReactionMode
    ) -> bool:
        """
        반응 성공 여부 판정
        
        Args:
            voice_detected: 음성 반응 감지 여부
            gaze_match: 시선 반응 감지 여부
            mode: 반응 판정 모드
            
        Returns:
            성공 여부
        """
        if mode == ReactionMode.VOICE_ONLY:
            return voice_detected
        elif mode == ReactionMode.GAZE_ONLY:
            return gaze_match
        elif mode == ReactionMode.OR:
            return voice_detected or gaze_match
        elif mode == ReactionMode.AND:
            return voice_detected and gaze_match
        elif mode == ReactionMode.WEIGHTED:
            # 가중 평균 (향후 구현, mvp 아님.)
            # 임시로 OR 로직 사용
            return voice_detected or gaze_match
        else:
            # 기본값: OR
            return voice_detected or gaze_match
