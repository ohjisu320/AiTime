# services/name_non_facing/app/core/gaze_calculator.py
"""
시선 벡터 계산기

Euler Angles (yaw, pitch, roll)를 3D 시선 벡터로 변환하고,
시선 벡터와 위치 벡터 사이의 각도를 계산합니다.

설계 의도:
    1. 6DRepNet360 출력 → 3D 시선 벡터 변환
    2. 아이 → 부모 위치 벡터 계산
    3. 시선-위치 각도 계산 (반응 판정용)

좌표계:
    - X: 오른쪽이 양수
    - Y: 아래가 양수 (이미지 좌표계)
    - Z: 앞(카메라 방향)이 양수

Reference:
    - 1409_뒤통수_미탐지문제로_yolohead및6drepnet360 모델 조합으로 변경.md
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np
import logging

from app.models.head_pose_6d import HeadPose6D
from app.models.head_detector import BoundingBox

logger = logging.getLogger(__name__)


def euler_to_gaze_vector(yaw_deg: float, pitch_deg: float) -> np.ndarray:
    """
    Euler angles (yaw, pitch)를 3D 시선 벡터로 변환
    
    Args:
        yaw_deg: 좌우 회전 각도 (도), 왼쪽이 양수
        pitch_deg: 상하 회전 각도 (도), 아래가 양수
        
    Returns:
        정규화된 3D 시선 벡터 [x, y, z]
        
    좌표계:
        - 정면(yaw=0, pitch=0): [0, 0, 1]
        - 왼쪽 90°(yaw=90): [1, 0, 0]
        - 오른쪽 90°(yaw=-90): [-1, 0, 0]
        - 뒤통수(yaw=180): [0, 0, -1]
    """
    yaw = np.radians(yaw_deg)
    pitch = np.radians(pitch_deg)
    
    # 시선 벡터 계산
    # 초기 시선 방향: +Z (정면, 카메라를 향함)
    # yaw: Y축 기준 회전 (좌우)
    # pitch: X축 기준 회전 (상하)
    
    x = np.cos(pitch) * np.sin(yaw)
    y = np.sin(pitch)
    z = np.cos(pitch) * np.cos(yaw)
    
    gaze_vector = np.array([x, y, z])
    norm = np.linalg.norm(gaze_vector)
    
    if norm > 1e-6:
        return gaze_vector / norm
    return np.array([0, 0, 1])  # 기본값: 정면


def compute_position_vector_2d(
    child_center: Tuple[float, float],
    parent_center: Tuple[float, float],
    frame_shape: Tuple[int, int] = None
) -> np.ndarray:
    """
    아이 → 부모 방향의 위치 벡터 (2D, z=0)
    
    Args:
        child_center: 아이 머리 중심 (픽셀)
        parent_center: 부모 머리 중심 (픽셀)
        frame_shape: (height, width) 정규화용 (옵션)
        
    Returns:
        정규화된 3D 위치 벡터 [dx, dy, 0]
    """
    dx = parent_center[0] - child_center[0]
    dy = parent_center[1] - child_center[1]
    
    # 프레임 크기로 정규화 (옵션)
    if frame_shape is not None:
        height, width = frame_shape[:2]
        dx /= width
        dy /= height
    
    # z=0으로 가정 (같은 평면)
    position_vector = np.array([dx, dy, 0.0])
    norm = np.linalg.norm(position_vector)
    
    if norm > 1e-6:
        return position_vector / norm
    return np.array([0, 0, 1])  # 기본값: 정면


def compute_position_vector_3d(
    child_center: Tuple[float, float],
    parent_center: Tuple[float, float],
    child_depth: float = 0.0,
    parent_depth: float = 0.0
) -> np.ndarray:
    """
    아이 → 부모 방향의 위치 벡터 (3D)
    
    Args:
        child_center: 아이 머리 중심 (정규화 또는 픽셀)
        parent_center: 부모 머리 중심 (정규화 또는 픽셀)
        child_depth: 아이 깊이 (z좌표, bbox 크기로 추정 가능)
        parent_depth: 부모 깊이 (z좌표)
        
    Returns:
        정규화된 3D 위치 벡터 [dx, dy, dz]
    """
    dx = parent_center[0] - child_center[0]
    dy = parent_center[1] - child_center[1]
    dz = parent_depth - child_depth
    
    position_vector = np.array([dx, dy, dz])
    norm = np.linalg.norm(position_vector)
    
    if norm > 1e-6:
        return position_vector / norm
    return np.array([0, 0, 1])


def angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    두 벡터 사이 각도 (도)
    
    Args:
        v1: 첫 번째 벡터
        v2: 두 번째 벡터
        
    Returns:
        각도 (0° ~ 180°)
    """
    # 정규화
    v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)
    v2_norm = v2 / (np.linalg.norm(v2) + 1e-8)
    
    # 내적
    cos_angle = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
    
    # 각도 (라디안 → 도)
    angle_rad = np.arccos(cos_angle)
    return np.degrees(angle_rad)


def compute_gaze_angle(
    head_pose: HeadPose6D,
    child_center: Tuple[float, float],
    parent_center: Tuple[float, float],
    frame_shape: Tuple[int, int] = None
) -> float:
    """
    시선 벡터와 위치 벡터 사이 각도 계산
    
    아이가 부모 방향을 보고 있으면 각도가 작고 (0에 가까움),
    다른 방향을 보고 있으면 각도가 큽니다.
    
    Args:
        head_pose: 아이의 Head Pose (yaw, pitch, roll)
        child_center: 아이 머리 중심 (픽셀)
        parent_center: 부모 머리 중심 (픽셀)
        frame_shape: (height, width) 옵션
        
    Returns:
        시선-위치 각도 (도, 0° ~ 180°)
    """
    # 시선 벡터
    gaze_vector = head_pose.to_gaze_vector()
    
    # 위치 벡터
    position_vector = compute_position_vector_2d(
        child_center=child_center,
        parent_center=parent_center,
        frame_shape=frame_shape
    )
    
    # 각도 계산
    angle = angle_between_vectors(gaze_vector, position_vector)
    
    return angle


@dataclass
class GazeAnalysisResult:
    """시선 분석 결과"""
    gaze_vector: np.ndarray       # 시선 벡터 [x, y, z]
    position_vector: np.ndarray   # 위치 벡터 [x, y, z]
    angle_deg: float              # 시선-위치 각도 (도)
    is_looking_at_parent: bool    # 부모 방향 시선 여부
    head_pose: HeadPose6D         # 원본 Head Pose
    
    def __str__(self) -> str:
        direction = "O" if self.is_looking_at_parent else "X"
        return (
            f"GazeAnalysis(yaw={self.head_pose.yaw:.1f}°, "
            f"pitch={self.head_pose.pitch:.1f}°, "
            f"angle={self.angle_deg:.1f}°, "
            f"looking={direction})"
        )


def analyze_gaze(
    head_pose: HeadPose6D,
    child_center: Tuple[float, float],
    parent_center: Tuple[float, float],
    frame_shape: Tuple[int, int] = None,
    angle_threshold_deg: float = 20.0
) -> GazeAnalysisResult:
    """
    시선 분석 수행
    
    Args:
        head_pose: 아이의 Head Pose
        child_center: 아이 머리 중심 (픽셀)
        parent_center: 부모 머리 중심 (픽셀)
        frame_shape: (height, width) 옵션
        angle_threshold_deg: 시선 판정 임계값 (도)
        
    Returns:
        GazeAnalysisResult
    """
    # 벡터 계산
    gaze_vector = head_pose.to_gaze_vector()
    position_vector = compute_position_vector_2d(
        child_center=child_center,
        parent_center=parent_center,
        frame_shape=frame_shape
    )
    
    # 각도 계산
    angle = angle_between_vectors(gaze_vector, position_vector)
    
    # 판정
    is_looking = angle <= angle_threshold_deg
    
    return GazeAnalysisResult(
        gaze_vector=gaze_vector,
        position_vector=position_vector,
        angle_deg=angle,
        is_looking_at_parent=is_looking,
        head_pose=head_pose
    )


def find_reaction_start_frame(
    gaze_results: list,
    angle_threshold_deg: float = 20.0,
    stabilize_frames: int = 3
) -> Optional[int]:
    """
    반응 시작 프레임 찾기
    
    각도가 임계치 이하로 안정화되기 시작하는 프레임을 찾습니다.
    
    Args:
        gaze_results: GazeAnalysisResult 또는 (frame_idx, angle) 목록
        angle_threshold_deg: 시선 판정 임계값 (도)
        stabilize_frames: 안정화 판정에 필요한 연속 프레임 수
        
    Returns:
        반응 시작 프레임 인덱스 또는 None
    """
    if len(gaze_results) < stabilize_frames:
        return None
    
    # 각도 목록 추출
    angles = []
    for result in gaze_results:
        if isinstance(result, GazeAnalysisResult):
            angles.append(result.angle_deg)
        elif isinstance(result, tuple):
            angles.append(result[1])  # (frame_idx, angle)
        else:
            angles.append(float(result))
    
    # 연속으로 임계치 이하인 구간 찾기
    consecutive_count = 0
    
    for i, angle in enumerate(angles):
        if angle <= angle_threshold_deg:
            consecutive_count += 1
            if consecutive_count >= stabilize_frames:
                # 안정화 시작점 반환
                return i - stabilize_frames + 1
        else:
            consecutive_count = 0
    
    return None


def estimate_depth_from_bbox(
    bbox: BoundingBox,
    reference_size: float = 0.15
) -> float:
    """
    bbox 크기로 깊이(거리) 추정
    
    큰 bbox = 가까움 (작은 depth)
    작은 bbox = 멀음 (큰 depth)
    
    Args:
        bbox: 머리 bbox
        reference_size: 기준 크기 (정규화)
        
    Returns:
        추정 깊이 (작을수록 가까움)
    """
    # bbox 면적 기준
    area = bbox.area
    
    if area > 0:
        # 면적의 역수 (정규화)
        depth = reference_size / np.sqrt(area)
    else:
        depth = 1.0  # 기본값
    
    return depth
