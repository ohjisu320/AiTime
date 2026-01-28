# services/name_non_facing/app/pipeline/orchestrator.py
"""
파이프라인 오케스트레이터

Stage들의 실행 순서를 관리하고, 전체 파이프라인을 조율합니다.

설계 원칙:
    1. 단일 책임 (Single Responsibility)
       - Orchestrator: Stage 실행 순서 관리
       - Stage: 개별 작업 수행
       
    2. 구성 가능성 (Composability)
       - Stage 목록을 외부에서 주입
       - 테스트 시 특정 Stage만 실행 가능
       
    3. 일관된 에러 처리
       - Stage 실패 시 전체 상태를 FAILED로 변경
       - 부분 결과도 보존

Reference:
    - Pipeline Pattern: https://java-design-patterns.com/patterns/pipeline/
    - Orchestrator Pattern: https://docs.microsoft.com/en-us/azure/architecture/patterns/choreography
"""

from typing import List, Dict, Any
from datetime import datetime
import logging
import uuid

from app.pipeline.context import PipelineContext, PipelineStatus
from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.stages import (
    InputStage,
    TriggerStage,
    ReactionDetectStage,
    ResultStage,
)

logger = logging.getLogger(__name__)


class AudioPipelineOrchestrator:
    """
    오디오 파이프라인 오케스트레이터
    
    비디오/오디오 입력부터 음성 반응 분석까지의 파이프라인을 실행합니다.
    
    Default Stages:
        1. InputStage: 비디오에서 오디오 추출
        2. TriggerStage: 호명 감지
        3. ReactionDetectStage: 음성 반응 감지
        4. ResultStage: 최종 결과 산출
    
    Usage:
        # 기본 사용
        orchestrator = AudioPipelineOrchestrator()
        result = orchestrator.run(
            video_path="video.mp4",
            child_name="정현"
        )
        
        # 커스텀 Stage 사용
        orchestrator = AudioPipelineOrchestrator(stages=[
            InputStage(),
            TriggerStage(),
            # ReactionDetectStage 생략
            ResultStage(),
        ])
    """
    
    def __init__(self, stages: List[BaseStage] = None):
        """
        Args:
            stages: 실행할 Stage 목록 (None이면 기본 구성)
        """
        if stages is None:
            stages = self._create_default_stages()
        
        self._stages = stages
        logger.info(
            f"🩵 AudioPipelineOrchestrator 초기화: "
            f"{[s.name for s in stages]}"
        )
    
    def _create_default_stages(self) -> List[BaseStage]:
        """기본 Stage 구성 생성"""
        return [
            InputStage(),
            TriggerStage(),
            ReactionDetectStage(),
            ResultStage(),
        ]
    
    def run(
        self,
        video_path: str,
        child_name: str,
        child_nickname: str = None,
        request_id: str = None
    ) -> Dict[str, Any]:
        """
        파이프라인 실행
        
        Args:
            video_path: 비디오 파일 경로
            child_name: 아이 이름
            request_id: 요청 ID (None이면 자동 생성)
            
        Returns:
            최종 결과 딕셔너리
        """
        # 요청 ID 생성
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # 컨텍스트 초기화
        context = PipelineContext(
            request_id=request_id,
            video_path=video_path,
            child_name=child_name,
            status=PipelineStatus.RUNNING
        )
        
        logger.info("=" * 60)
        logger.info(f"🩵🩵🩵 파이프라인 시작: {request_id}")
        logger.info(f"   비디오: {video_path}")
        logger.info(f"   아이 이름: {child_name}")
        logger.info("=" * 60)
        
        # Stage 순차 실행
        try:
            for stage in self._stages:
                context = stage.run(context)
            
            context.status = PipelineStatus.COMPLETED
            context.completed_at = datetime.now()
            
        except Exception as e:
            context.status = PipelineStatus.FAILED
            context.completed_at = datetime.now()
            logger.error(f"✖️✖️✖️ 파이프라인 실패: {e}")
            # 부분 결과라도 반환
        
        # 최종 결과 생성
        result = context.to_result()
        
        # 결과 요약 로깅
        logger.info("=" * 60)
        logger.info(f"🩵🩵🩵 파이프라인 완료: {context.status.value}")
        
        total_time = sum(context.processing_times.values())
        logger.info(f"   총 처리 시간: {total_time:.2f}s")
        
        for stage_name, elapsed in context.processing_times.items():
            pct = (elapsed / total_time * 100) if total_time > 0 else 0
            logger.info(f"   - {stage_name}: {elapsed:.2f}s ({pct:.1f}%)")
        
        if context.errors:
            logger.error(f"   에러: {context.errors}")
        if context.warnings:
            logger.warning(f"   경고: {context.warnings}")
        
        logger.info("=" * 60)
        
        return result
    
    def run_with_context(
        self,
        context: PipelineContext
    ) -> PipelineContext:
        """
        기존 컨텍스트로 파이프라인 실행
        
        이미 초기화된 컨텍스트를 사용하여 파이프라인을 실행합니다.
        테스트나 재시도 시 유용합니다.
        
        Args:
            context: 기존 컨텍스트
            
        Returns:
            업데이트된 컨텍스트
        """
        context.status = PipelineStatus.RUNNING
        
        try:
            for stage in self._stages:
                context = stage.run(context)
            
            context.status = PipelineStatus.COMPLETED
            context.completed_at = datetime.now()
            
        except Exception as e:
            context.status = PipelineStatus.FAILED
            context.completed_at = datetime.now()
            logger.error(f"✖️✖️✖️ 파이프라인 실패: {e}")
        
        return context


def create_audio_pipeline() -> AudioPipelineOrchestrator:
    """
    기본 오디오 파이프라인 생성 (편의 함수)
    
    Usage:
        pipeline = create_audio_pipeline()
        result = pipeline.run(video_path="...", child_name="...")
    """
    return AudioPipelineOrchestrator()
