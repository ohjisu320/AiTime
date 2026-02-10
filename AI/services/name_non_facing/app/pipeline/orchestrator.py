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

from typing import List, Dict, Any, Optional
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
from app.pipeline.stages.head_detect_stage import HeadDetectStage
from app.pipeline.stages.child_analysis_stage import ChildAnalysisStage
# [deprecated] MediaPipe 기반 Stage
# from app.pipeline.stages.face_detect_stage import FaceDetectStage

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


class FullPipelineOrchestrator:
    """
    통합 파이프라인 오케스트레이터 (Audio + Vision)
    
    비디오에서 오디오와 비전 분석을 모두 수행합니다.
    YOLO Head + 6DRepNet360 기반으로 360° 머리 포즈 추정 지원.
    
    Default Stages:
        1. InputStage: 비디오에서 오디오 추출
        2. HeadDetectStage: 머리 탐지 및 위치 벡터 생성 (YOLO 기반)
        3. TriggerStage: 호명 감지
        4. ChildAnalysisStage: 시선 분석 (6DRepNet360 기반)
        5. ReactionDetectStage: 음성 반응 감지 (Audio)
        6. ResultStage: 최종 결과 산출 (통합)
    
    Usage:
        orchestrator = FullPipelineOrchestrator()
        result = orchestrator.run(
            video_path="video.mp4",
            child_name="은연"
        )
    
    Reference:
        - 1409_뒤통수_미탐지문제로_yolohead및6drepnet360 모델 조합으로 변경.md
    """
    
    def __init__(self, stages: List[BaseStage] = None, target_fps: int = None, skip_audio: bool = False, continue_on_error: bool = False):
        """
        Args:
            stages: 실행할 Stage 목록 (None이면 기본 구성)
            target_fps: 프레임 추출 FPS (None이면 config 값 사용, 0이면 원본 FPS 유지)
            skip_audio: 오디오 반응 분석(ReactionDetectStage) 건너뛰기
            continue_on_error: True면 개별 Stage 실패 시 건너뛰고 계속 진행
        """
        self._target_fps = target_fps
        self._skip_audio = skip_audio
        self._continue_on_error = continue_on_error
        self._context: Optional[PipelineContext] = None  # 마지막 실행 context 저장
        
        if stages is None:
            stages = self._create_default_stages()
        
        self._stages = stages
        logger.info(
            f"🩷 FullPipelineOrchestrator 초기화: "
            f"{[s.name for s in stages]}"
        )
    
    @property
    def context(self) -> Optional[PipelineContext]:
        """마지막 파이프라인 실행의 context (시각화 등에서 사용)"""
        return self._context
    
    def _create_default_stages(self) -> List[BaseStage]:
        """기본 Stage 구성 생성 (Audio + Vision, YOLO + 6DRepNet360)"""
        stages = [
            InputStage(),                                    # 오디오 추출
            HeadDetectStage(target_fps=self._target_fps),    # 머리 탐지 (YOLO)
            TriggerStage(),                                  # 호명 감지
            ChildAnalysisStage(),                            # 시선 분석 (6DRepNet360)
        ]
        
        if not self._skip_audio:
            stages.append(ReactionDetectStage())             # 음성 반응 감지 (Audio)
        
        stages.append(ResultStage())                         # 통합 결과 산출
        return stages
    
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
            child_nickname: 아이 별명 (선택)
            request_id: 요청 ID (None이면 자동 생성)
            
        Returns:
            최종 결과 딕셔너리
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        context = PipelineContext(
            request_id=request_id,
            video_path=video_path,
            child_name=child_name,
            child_nickname=child_nickname,
            status=PipelineStatus.RUNNING
        )
        self._context = context  # 시각화 등에서 접근할 수 있도록 저장
        
        logger.info("=" * 60)
        logger.info(f"🩷🩷🩷 통합 파이프라인 시작: {request_id}")
        logger.info(f"   비디오: {video_path}")
        logger.info(f"   아이 이름: {child_name}")
        logger.info("=" * 60)
        
        if self._continue_on_error:
            # Stage별 에러를 건너뛰고 계속 진행
            for stage in self._stages:
                try:
                    context = stage.run(context)
                except Exception as e:
                    logger.error(
                        f"⚠️ {stage.name} 실패 (건너뜀): {e}",
                    )
                    context.errors.append(
                        f"[{stage.name}] {e}"
                    )
            # 에러가 있었으면 PARTIAL, 없으면 COMPLETED
            if context.errors:
                context.status = PipelineStatus.FAILED
            else:
                context.status = PipelineStatus.COMPLETED
            context.completed_at = datetime.now()
        else:
            try:
                for stage in self._stages:
                    context = stage.run(context)
                context.status = PipelineStatus.COMPLETED
                context.completed_at = datetime.now()
            except Exception as e:
                context.status = PipelineStatus.FAILED
                context.completed_at = datetime.now()
                logger.error(
                    f"✖️✖️✖️ 파이프라인 실패: {e}",
                    exc_info=True,
                )
        
        result = context.to_result()
        
        # 결과 요약 로깅
        logger.info("=" * 60)
        logger.info(f"🩷🩷🩷 파이프라인 완료: {context.status.value}")
        
        total_time = sum(context.processing_times.values())
        logger.info(f"   총 처리 시간: {total_time:.2f}s")
        
        for stage_name, elapsed in context.processing_times.items():
            pct = (elapsed / total_time * 100) if total_time > 0 else 0
            logger.info(f"   - {stage_name}: {elapsed:.2f}s ({pct:.1f}%)")
        
        # Trial별 결과 요약
        if context.trial_results:
            success_count = sum(1 for tr in context.trial_results if tr.success)
            logger.info(
                f"   결과: {success_count}/{len(context.trial_results)} 시도 성공"
            )
            for tr in context.trial_results:
                status = "✅" if tr.success else "❌"
                latency_str = f"{tr.latency_s:.2f}s" if tr.latency_s else "N/A"
                logger.info(
                    f"     [시도 {tr.trial_index}] {status} "
                    f"Latency: {latency_str}, "
                    f"Voice: {tr.voice_detected}, Gaze: {tr.gaze_match}"
                )
        
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
            logger.error(f"✖️✖️✖️ 파이프라인 실패: {e}", exc_info=True)
        
        return context


def create_full_pipeline() -> FullPipelineOrchestrator:
    """
    통합 파이프라인 생성 (Audio + Vision)
    
    Usage:
        pipeline = create_full_pipeline()
        result = pipeline.run(video_path="...", child_name="...")
    """
    return FullPipelineOrchestrator()
