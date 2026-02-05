# services/name_non_facing/app/core/gaze_analyzer.py
"""
시선 반응 분석기

호명 후 아이의 시선 반응(고개 돌림)을 분석합니다.

설계 의도:
    1. 비대면(Non-Facing) 호명반응
       - 호명 전: 아이는 부모를 보고 있지 않음
       - 호명 후: 고개를 돌려 부모를 봐야 반응 성공
       
    2. 안정화 기반 반응 감지
       - 임계치 이하 상태가 N프레임 연속 유지 = 안정화
       - 안정화 시작점 = 고개 돌림 시작점 (T_react)
       
    3. 시선 유지 시간 측정
       - 각도가 임계치 이하로 유지된 연속 시간

알고리즘:
    1. 호명 종료(T_start) 이후 프레임들을 순회
    2. 각 프레임: angle = angle(gaze_vector, position_vector)
    3. 연속 N개 프레임이 angle < threshold → 안정화 판정
    4. 안정화 시작점 = T_react
    5. 시선 유지 시간 = 임계치 이하 연속 유지 시간

Reference:
    - 필수참고_작업설계.md: 반응 정의
    - 1318_구현설계.md: 상세 알고리즘
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import logging

import numpy as np

from app.core.angle_calculator import (
    angle_between_vectors_deg,
    find_stable_crossing_index
)
from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class GazeFrameResult:
    """프레임별 시선 분석 결과"""
    timestamp: float                    # 프레임 시간 (초)
    gaze_vector: np.ndarray             # 시선 방향 벡터
    position_vector: np.ndarray         # 부모 방향 벡터
    angle_deg: float                    # 두 벡터 사이 각도 (도)
    is_looking_at_parent: bool          # 임계치 이하 여부
    head_yaw_deg: float                 # 머리 Yaw 각도
    head_pitch_deg: float               # 머리 Pitch 각도
    child_detected: bool                # 아이 얼굴 탐지 여부
    
    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            "timestamp": self.timestamp,
            "gaze_vector": self.gaze_vector.tolist() if self.gaze_vector is not None else None,
            "position_vector": self.position_vector.tolist() if self.position_vector is not None else None,
            "angle_deg": self.angle_deg,
            "is_looking_at_parent": self.is_looking_at_parent,
            "head_yaw_deg": self.head_yaw_deg,
            "head_pitch_deg": self.head_pitch_deg,
            "child_detected": self.child_detected
        }


@dataclass
class GazeReactionResult:
    """시선 반응 분석 결과 (Trial별)"""
    detected: bool                      # 시선 반응 감지 여부
    latency_sec: Optional[float]        # 반응 지연 시간 (T_react - T_start)
    duration_sec: Optional[float]       # 시선 유지 시간
    yaw_deg: Optional[float]            # 반응 시점 Yaw 각도
    pitch_deg: Optional[float]          # 반응 시점 Pitch 각도
    min_angle_deg: Optional[float]      # 최소 도달 각도
    fail_reason: Optional[str]          # 실패 사유
    t_start: Optional[float] = None     # 호명 종료 시점
    t_react: Optional[float] = None     # 반응 시작 시점
    
    @property
    def match(self) -> bool:
        """ResultStage 호환용"""
        return self.detected
    
    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            "detected": self.detected,
            "latency_sec": self.latency_sec,
            "duration_sec": self.duration_sec,
            "yaw_deg": self.yaw_deg,
            "pitch_deg": self.pitch_deg,
            "min_angle_deg": self.min_angle_deg,
            "fail_reason": self.fail_reason,
            "t_start": self.t_start,
            "t_react": self.t_react
        }


class GazeAnalyzer:
    """
    시선 반응 분석기
    
    호명 이벤트에 대해 아이의 시선 반응(고개 돌림)을 분석합니다.
    
    Usage:
        analyzer = GazeAnalyzer()
        result = analyzer.analyze_trial(
            gaze_results=frame_results,
            t_start=3.5,  # 호명 종료 시점
            timeout_sec=5.0
        )
        if result.detected:
            print(f"반응 감지! Latency: {result.latency_sec}s")
    """
    
    def __init__(
        self,
        threshold_deg: Optional[float] = None,
        stabilize_frames: Optional[int] = None,
        timeout_sec: Optional[float] = None
    ):
        """
        Args:
            threshold_deg: 시선 각도 임계치 (도)
            stabilize_frames: 안정화 판정 프레임 수
            timeout_sec: 반응 대기 시간
        """
        settings = get_settings()
        self.threshold_deg = threshold_deg or settings.GAZE_ANGLE_THRESHOLD_DEG
        self.stabilize_frames = stabilize_frames or settings.GAZE_STABILIZE_FRAMES
        self.timeout_sec = timeout_sec or settings.REACTION_TIMEOUT_SEC
    
    def analyze_trial(
        self,
        gaze_results: List[GazeFrameResult],
        t_start: float,
        timeout_sec: Optional[float] = None
    ) -> GazeReactionResult:
        """
        단일 Trial에 대한 시선 반응 분석
        
        Args:
            gaze_results: 프레임별 시선 분석 결과
            t_start: 호명 종료 시점 (초)
            timeout_sec: 반응 대기 시간 (None이면 기본값)
            
        Returns:
            GazeReactionResult
        """
        timeout = timeout_sec or self.timeout_sec
        t_end = t_start + timeout
        
        # 1. 분석 구간 필터링 (T_start ~ T_start + timeout)
        window = [
            g for g in gaze_results
            if t_start <= g.timestamp <= t_end
        ]
        
        if not window:
            logger.warning(f"분석 구간에 프레임 없음: {t_start:.2f}s ~ {t_end:.2f}s")
            return GazeReactionResult(
                detected=False,
                latency_sec=None,
                duration_sec=None,
                yaw_deg=None,
                pitch_deg=None,
                min_angle_deg=None,
                fail_reason="no_frames_in_window",
                t_start=t_start
            )
        
        # 2. 아이 얼굴 탐지 확인
        detected_frames = [g for g in window if g.child_detected]
        if not detected_frames:
            logger.warning("분석 구간에서 아이 얼굴 미탐지")
            return GazeReactionResult(
                detected=False,
                latency_sec=None,
                duration_sec=None,
                yaw_deg=None,
                pitch_deg=None,
                min_angle_deg=None,
                fail_reason="face_not_detected",
                t_start=t_start
            )
        
        # 3. 각도 시퀀스 추출 (탐지된 프레임만)
        angles = [g.angle_deg for g in detected_frames]
        timestamps = [g.timestamp for g in detected_frames]
        
        # 4. 안정적 교차점 찾기
        stable_idx = find_stable_crossing_index(
            angles=angles,
            threshold_deg=self.threshold_deg,
            stabilize_count=self.stabilize_frames
        )
        
        if stable_idx == -1:
            # 안정화 실패 = 반응 없음
            logger.info(
                f"시선 반응 없음: 각도 범위 "
                f"{min(angles):.1f}° ~ {max(angles):.1f}° "
                f"(임계치: {self.threshold_deg}°)"
            )
            return GazeReactionResult(
                detected=False,
                latency_sec=None,
                duration_sec=None,
                yaw_deg=None,
                pitch_deg=None,
                min_angle_deg=min(angles) if angles else None,
                fail_reason="no_stable_gaze",
                t_start=t_start
            )
        
        # 5. 반응 시점 (T_react) 및 Latency 계산
        t_react = timestamps[stable_idx]
        latency = t_react - t_start
        
        # 6. 시선 유지 시간 계산
        duration = 0.0
        for i in range(stable_idx, len(detected_frames)):
            if detected_frames[i].is_looking_at_parent:
                duration = detected_frames[i].timestamp - t_react
            else:
                break
        
        # 약간의 보정: 최소 1프레임 시간 보장
        if duration == 0.0 and stable_idx < len(detected_frames):
            frame_interval = (
                (timestamps[-1] - timestamps[0]) / len(timestamps)
                if len(timestamps) > 1 else 0.1
            )
            duration = frame_interval
        
        # 7. 결과 생성
        react_frame = detected_frames[stable_idx]
        
        logger.info(
            f"🩷 시선 반응 감지! "
            f"Latency: {latency:.2f}s, Duration: {duration:.2f}s, "
            f"MinAngle: {min(angles):.1f}°"
        )
        
        return GazeReactionResult(
            detected=True,
            latency_sec=latency,
            duration_sec=duration,
            yaw_deg=react_frame.head_yaw_deg,
            pitch_deg=react_frame.head_pitch_deg,
            min_angle_deg=min(angles),
            fail_reason=None,
            t_start=t_start,
            t_react=t_react
        )
    
    def analyze_all_trials(
        self,
        gaze_results: List[GazeFrameResult],
        t_starts: List[float],
        timeout_sec: Optional[float] = None
    ) -> List[GazeReactionResult]:
        """
        모든 Trial에 대한 시선 반응 분석
        
        Args:
            gaze_results: 전체 프레임별 시선 분석 결과
            t_starts: 호명 종료 시점 목록
            timeout_sec: 반응 대기 시간
            
        Returns:
            Trial별 GazeReactionResult 목록
        """
        results = []
        
        for i, t_start in enumerate(t_starts):
            logger.info(f"[시도 {i+1}] 시선 반응 분석: T_start={t_start:.2f}s")
            result = self.analyze_trial(
                gaze_results=gaze_results,
                t_start=t_start,
                timeout_sec=timeout_sec
            )
            results.append(result)
        
        return results


def create_gaze_frame_result(
    timestamp: float,
    gaze_vector: Optional[np.ndarray],
    position_vector: Optional[np.ndarray],
    head_yaw_deg: float,
    head_pitch_deg: float,
    child_detected: bool,
    threshold_deg: float
) -> GazeFrameResult:
    """
    GazeFrameResult 생성 헬퍼
    
    Args:
        timestamp: 프레임 시간
        gaze_vector: 시선 벡터 (None이면 미탐지)
        position_vector: 부모 방향 벡터
        head_yaw_deg: 머리 Yaw 각도
        head_pitch_deg: 머리 Pitch 각도
        child_detected: 아이 탐지 여부
        threshold_deg: 각도 임계치
        
    Returns:
        GazeFrameResult
    """
    if not child_detected or gaze_vector is None or position_vector is None:
        return GazeFrameResult(
            timestamp=timestamp,
            gaze_vector=gaze_vector if gaze_vector is not None else np.zeros(3),
            position_vector=position_vector if position_vector is not None else np.zeros(3),
            angle_deg=180.0,  # 최대 각도
            is_looking_at_parent=False,
            head_yaw_deg=head_yaw_deg,
            head_pitch_deg=head_pitch_deg,
            child_detected=child_detected
        )
    
    angle_deg = angle_between_vectors_deg(gaze_vector, position_vector)
    is_looking = angle_deg <= threshold_deg
    
    return GazeFrameResult(
        timestamp=timestamp,
        gaze_vector=gaze_vector,
        position_vector=position_vector,
        angle_deg=angle_deg,
        is_looking_at_parent=is_looking,
        head_yaw_deg=head_yaw_deg,
        head_pitch_deg=head_pitch_deg,
        child_detected=child_detected
    )
