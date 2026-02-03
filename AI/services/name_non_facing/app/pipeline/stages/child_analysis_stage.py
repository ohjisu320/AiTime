# services/name_non_facing/app/pipeline/stages/child_analysis_stage.py
"""
아이 분석 Stage (Vision) - 6DRepNet360 기반

아이의 시선(고개 방향)을 분석하여 부모 방향을 향하는지 확인합니다.
360° 머리 포즈 추정을 통해 뒤통수 상태에서도 분석 가능합니다.

설계 의도:
    1. 시선 벡터 추출
       - 6DRepNet360 Euler → 시선 벡터 변환
       - yaw/pitch에서 3D 방향 벡터 생성
       
    2. 위치 벡터와 비교
       - 시선 벡터 ↔ 부모 방향 벡터 각도 계산
       - 임계치(20°) 이하면 "부모를 보고 있음"
       
    3. 프레임별 결과 저장
       - 이후 GazeAnalyzer가 Trial별 분석

Reference:
    - 1409_뒤통수_미탐지문제로_yolohead및6drepnet360 모델 조합으로 변경.md
    - 6DRepNet360: 360° Head Pose Estimation
"""

from typing import Optional, List, Tuple
import logging

import numpy as np

from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.context import PipelineContext
from app.models.head_pose_6d import HeadPoseEstimator6D, HeadPose6D
from app.core.gaze_calculator import (
    compute_position_vector_2d,
    compute_gaze_angle,
)
from app.core.gaze_analyzer import (
    GazeFrameResult, GazeAnalyzer,
    create_gaze_frame_result
)
from app.config import get_settings

logger = logging.getLogger(__name__)


class ChildAnalysisStage(BaseStage):
    """
    아이 시선 분석 Stage (6DRepNet360 기반)
    
    프레임별로 아이의 시선 방향을 분석하고,
    각 호명 이벤트에 대한 시선 반응을 감지합니다.
    
    MediaPipe와 달리 360° 범위에서 분석 가능합니다.
    
    Input:
        - context.frames: 비디오 프레임
        - context.frame_timestamps: 프레임 타임스탬프
        - context.child_detections: 아이 탐지 결과 (HeadDetection)
        - context.parent_positions: 부모 위치
        - context.name_call_events: 호명 이벤트 목록
        
    Output:
        - context.gaze_frame_results: 프레임별 시선 분석 결과
        - context.gaze_results: Trial별 시선 반응 결과
        - context.head_pose_6d_results: 6DRepNet360 포즈 결과
    """
    
    def __init__(
        self,
        head_pose_estimator: HeadPoseEstimator6D = None,
        gaze_analyzer: GazeAnalyzer = None
    ):
        """
        Args:
            head_pose_estimator: 360° Head Pose 추정기 (None이면 자동 생성)
            gaze_analyzer: 시선 분석기 (None이면 자동 생성)
        """
        self._settings = get_settings()
        self._head_pose_estimator = head_pose_estimator or HeadPoseEstimator6D()
        self._gaze_analyzer = gaze_analyzer or GazeAnalyzer()
    
    @property
    def name(self) -> str:
        return "ChildAnalysisStage"
    
    def validate(self, context: PipelineContext) -> Optional[str]:
        """프레임 데이터 존재 여부 검증"""
        if not context.frames:
            return "프레임 데이터가 없습니다. FaceDetectStage를 먼저 실행하세요."
        return None
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        시선 분석 수행 (6DRepNet360)
        
        Process:
            1. 각 프레임에서 아이 머리 ROI로 6DRepNet360 추론
            2. Euler → 시선 벡터 변환
            3. 위치 벡터와 각도 비교
            4. Trial별 시선 반응 감지
        """
        logger.info(f"🩷 시선 분석 시작 (6DRepNet360, {len(context.frames)}프레임)")
        
        # 1. 프레임별 시선 분석
        gaze_frame_results = []
        head_pose_6d_results = []  # 6DRepNet360 결과 저장
        
        for i, (frame, ts) in enumerate(
            zip(context.frames, context.frame_timestamps)
        ):
            # 해당 시간의 아이 탐지 결과 (HeadDetection)
            child_detection = self._get_child_at_time(
                context.child_detections, ts
            )
            
            # 부모 위치
            parent_pos = self._get_parent_at_time(
                context.parent_positions, ts
            )
            
            # 시선 분석
            result, head_pose = self._analyze_frame_6d(
                frame=frame,
                timestamp=ts,
                child_detection=child_detection,
                parent_position=parent_pos,
                frame_width=context.frame_width,
                frame_height=context.frame_height
            )
            gaze_frame_results.append(result)
            head_pose_6d_results.append((ts, head_pose))
        
        context.gaze_frame_results = gaze_frame_results
        context.head_pose_6d_results = head_pose_6d_results
        
        # 통계 로깅
        child_detected_count = sum(
            1 for r in gaze_frame_results if r.child_detected
        )
        looking_count = sum(
            1 for r in gaze_frame_results if r.is_looking_at_parent
        )
        
        logger.info(
            f"🩷 프레임별 분석 완료: "
            f"아이탐지 {child_detected_count}/{len(gaze_frame_results)}, "
            f"부모응시 {looking_count}/{len(gaze_frame_results)}"
        )
        
        # 2. Trial별 시선 반응 분석
        if context.name_call_events:
            t_starts = [event.end_sec for event in context.name_call_events]
            
            gaze_reactions = self._gaze_analyzer.analyze_all_trials(
                gaze_results=gaze_frame_results,
                t_starts=t_starts,
                timeout_sec=self._settings.REACTION_TIMEOUT_SEC
            )
            context.gaze_results = gaze_reactions
            
            # 결과 로깅
            success_count = sum(1 for r in gaze_reactions if r.detected)
            logger.info(
                f"🩷 시선 반응 분석 완료: "
                f"{success_count}/{len(gaze_reactions)} 시도 반응 감지"
            )
        else:
            context.gaze_results = []
            logger.warning("호명 이벤트 없음, 시선 반응 분석 생략")
        
        return context
    
    def _analyze_frame_6d(
        self,
        frame: np.ndarray,
        timestamp: float,
        child_detection,
        parent_position: Tuple[float, float],
        frame_width: int,
        frame_height: int
    ) -> Tuple[GazeFrameResult, Optional[HeadPose6D]]:
        """
        단일 프레임 시선 분석 (6DRepNet360)
        
        Args:
            frame: 비디오 프레임
            timestamp: 프레임 시간
            child_detection: 아이 HeadDetection 또는 None
            parent_position: 부모 위치 (픽셀)
            frame_width, frame_height: 프레임 크기
            
        Returns:
            (GazeFrameResult, HeadPose6D or None)
        """
        # 아이 미탐지
        if child_detection is None:
            return create_gaze_frame_result(
                timestamp=timestamp,
                gaze_vector=None,
                position_vector=None,
                head_yaw_deg=0.0,
                head_pitch_deg=0.0,
                child_detected=False,
                threshold_deg=self._settings.GAZE_ANGLE_THRESHOLD_DEG
            ), None
        
        # 아이 머리 bounding box 추출
        bbox = child_detection.bbox
        
        # 6DRepNet360으로 Head Pose 추정
        head_pose = self._head_pose_estimator.estimate(frame, bbox)
        
        if head_pose is None:
            return create_gaze_frame_result(
                timestamp=timestamp,
                gaze_vector=None,
                position_vector=None,
                head_yaw_deg=0.0,
                head_pitch_deg=0.0,
                child_detected=True,  # 머리는 탐지됨
                threshold_deg=self._settings.GAZE_ANGLE_THRESHOLD_DEG
            ), None
        
        # Euler → 시선 벡터 변환
        gaze_vector = head_pose.to_gaze_vector()
        
        # 아이 중심 (픽셀)
        child_center_pixel = child_detection.center_pixel(
            frame_width, frame_height
        )
        
        # 위치 벡터 계산 (2D + z=0)
        position_vector = compute_position_vector_2d(
            child_center=child_center_pixel,
            parent_center=parent_position,
            frame_shape=(frame_height, frame_width)
        )
        
        # 시선-위치 각도 계산
        _ = compute_gaze_angle(
            head_pose=head_pose,
            child_center=child_center_pixel,
            parent_center=parent_position,
            frame_shape=(frame_height, frame_width)
        )
        
        return create_gaze_frame_result(
            timestamp=timestamp,
            gaze_vector=gaze_vector,
            position_vector=position_vector,
            head_yaw_deg=head_pose.yaw,
            head_pitch_deg=head_pose.pitch,
            child_detected=True,
            threshold_deg=self._settings.GAZE_ANGLE_THRESHOLD_DEG
        ), head_pose
    
    def _get_child_at_time(
        self,
        child_detections: List[Tuple[float, any]],
        timestamp: float
    ):
        """시간에 해당하는 아이 탐지 결과"""
        for ts, child in child_detections:
            if abs(ts - timestamp) < 0.001:
                return child
        return None
    
    def _get_parent_at_time(
        self,
        parent_positions: List[Tuple[float, Tuple[float, float]]],
        timestamp: float
    ) -> Tuple[float, float]:
        """시간에 해당하는 부모 위치"""
        for ts, pos in parent_positions:
            if abs(ts - timestamp) < 0.001:
                return pos
        # 기본값: 중앙
        return (self._settings.frame_width / 2, self._settings.frame_height / 2)
