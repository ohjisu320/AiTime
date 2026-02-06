# services/name_non_facing/app/core/vector_math.py
"""
벡터 연산 유틸리티

3D 벡터 연산을 위한 함수들을 제공합니다.
시선 벡터와 위치 벡터 계산에 사용됩니다.

설계 의도:
    1. NumPy 기반 고성능 연산
    2. 타입 안전성 (np.ndarray 타입 힌트)
    3. 엣지 케이스 처리 (영벡터, NaN 등)

Reference:
    - NumPy 벡터 연산: https://numpy.org/doc/stable/reference/routines.linalg.html
"""

from typing import Tuple, Union
import numpy as np


# 타입 별칭
Vector2D = np.ndarray  # shape: (2,)
Vector3D = np.ndarray  # shape: (3,)
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]


def normalize(v: np.ndarray) -> np.ndarray:
    """
    벡터를 단위 벡터로 정규화
    
    Args:
        v: 입력 벡터 (2D 또는 3D)
        
    Returns:
        정규화된 단위 벡터
        
    Note:
        - 영벡터 입력 시 영벡터 반환
        - NaN 처리 포함
    """
    norm = np.linalg.norm(v)
    if norm < 1e-10 or np.isnan(norm):
        return np.zeros_like(v)
    return v / norm


def magnitude(v: np.ndarray) -> float:
    """
    벡터의 크기(길이) 계산
    
    Args:
        v: 입력 벡터
        
    Returns:
        벡터 크기 (스칼라)
    """
    return float(np.linalg.norm(v))


def dot(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    두 벡터의 내적
    
    Args:
        v1, v2: 입력 벡터 (동일 차원)
        
    Returns:
        내적 값 (스칼라)
        
    수학적 정의:
        v1 · v2 = |v1| |v2| cos(θ)
    """
    return float(np.dot(v1, v2))


def cross(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
    """
    두 3D 벡터의 외적
    
    Args:
        v1, v2: 3D 벡터
        
    Returns:
        외적 결과 벡터 (3D)
        
    수학적 정의:
        v1 × v2 = |v1| |v2| sin(θ) n̂
        (n̂은 v1, v2에 수직인 단위 벡터, 오른손 법칙)
    """
    return np.cross(v1, v2)


def project_to_2d(v3d: np.ndarray) -> np.ndarray:
    """
    3D 벡터를 2D로 투영 (z 좌표 무시)
    
    Args:
        v3d: 3D 벡터 [x, y, z]
        
    Returns:
        2D 벡터 [x, y]
    """
    return v3d[:2].copy()


def extend_to_3d(v2d: np.ndarray, z: float = 0.0) -> np.ndarray:
    """
    2D 벡터를 3D로 확장
    
    Args:
        v2d: 2D 벡터 [x, y]
        z: z 좌표 값 (기본 0)
        
    Returns:
        3D 벡터 [x, y, z]
    """
    return np.array([v2d[0], v2d[1], z])


def vector_from_points(p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    """
    두 점 사이의 방향 벡터 (p1 → p2)
    
    Args:
        p1: 시작점
        p2: 끝점
        
    Returns:
        방향 벡터 (정규화되지 않음)
    """
    return p2 - p1


def direction_from_points(p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    """
    두 점 사이의 단위 방향 벡터 (p1 → p2)
    
    Args:
        p1: 시작점
        p2: 끝점
        
    Returns:
        단위 방향 벡터
    """
    return normalize(p2 - p1)


def midpoint(p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    """
    두 점의 중점
    
    Args:
        p1, p2: 두 점
        
    Returns:
        중점 좌표
    """
    return (p1 + p2) / 2.0


def compute_gaze_vector_from_ears_nose(
    left_ear: np.ndarray,
    right_ear: np.ndarray,
    nose_tip: np.ndarray
) -> np.ndarray:
    """
    귀와 코 좌표로부터 시선 벡터 계산 (레거시 - MediaPipe FaceMesh용)
    
    정의:
        양쪽 귀를 잇는 축에 직교하고, 코를 통과하는 단위 벡터
    
    Args:
        left_ear: 왼쪽 귀 좌표 [x, y, z]
        right_ear: 오른쪽 귀 좌표 [x, y, z]
        nose_tip: 코끝 좌표 [x, y, z]
        
    Returns:
        시선 방향 단위 벡터 [x, y, z]
        
    수학적 과정:
        1. ear_axis = right_ear - left_ear (귀 축)
        2. up_vector = [0, -1, 0] (이미지 좌표계 상향)
        3. gaze_raw = ear_axis × up_vector (외적)
        4. gaze_vector = normalize(gaze_raw)
    
    Note (2025-01-23 결정사항):
        현재 파이프라인에서 사용하지 않음. 6DRepNet360의 Euler angles 기반
        to_gaze_vector()가 더 정확하고 360° 지원.
        
        ViTPose COCO 키포인트(귀 idx 3,4)는 2D 전용 + 몸 레벨 정밀도라
        이 함수에 적합하지 않음. 기하학적 법선 벡터가 필요시
        MediaPipe FaceMesh(478점, 3D)가 더 적합.
        
        상세: docs/ViTPose_시선벡터_도입검토.md 참조
    """
    # 귀 축 벡터
    ear_axis = right_ear - left_ear
    
    # 상향 벡터 (이미지 좌표계: y축이 아래로 증가하므로 -y가 위)
    up_vector = np.array([0.0, -1.0, 0.0])
    
    # 외적으로 시선 방향 계산 (오른손 법칙)
    gaze_raw = cross(ear_axis, up_vector)
    
    # 정규화
    gaze_vector = normalize(gaze_raw)
    
    # 시선이 앞쪽을 향하도록 보정 (z가 양수면 카메라 반대 방향)
    # MediaPipe에서 z는 카메라 방향으로 음수가 가까움
    if gaze_vector[2] > 0:
        gaze_vector = -gaze_vector
    
    return gaze_vector


def compute_position_vector_2d(
    child_center: Tuple[float, float],
    parent_center: Tuple[float, float]
) -> np.ndarray:
    """
    아이 → 부모 방향의 2D 위치 벡터 계산
    
    Args:
        child_center: 아이 얼굴 중심 (cx, cy)
        parent_center: 부모 얼굴 중심 (cx, cy) 또는 카메라 중앙
        
    Returns:
        단위 방향 벡터 [x, y]
    """
    child = np.array(child_center)
    parent = np.array(parent_center)
    return normalize(parent - child)


def compute_position_vector_3d(
    child_center: Tuple[float, float],
    parent_center: Tuple[float, float],
    z: float = 0.0
) -> np.ndarray:
    """
    아이 → 부모 방향의 3D 위치 벡터 계산 (시선 벡터와 비교용)
    
    Args:
        child_center: 아이 얼굴 중심 (cx, cy)
        parent_center: 부모 얼굴 중심 (cx, cy)
        z: z 좌표 차이 (기본 0, 동일 평면 가정)
        
    Returns:
        단위 방향 벡터 [x, y, z]
    """
    child = np.array([child_center[0], child_center[1], 0.0])
    parent = np.array([parent_center[0], parent_center[1], z])
    return normalize(parent - child)


def is_valid_vector(v: np.ndarray) -> bool:
    """
    벡터가 유효한지 확인 (NaN, Inf, 영벡터 검사)
    
    Args:
        v: 검사할 벡터
        
    Returns:
        유효 여부
    """
    if v is None:
        return False
    if np.any(np.isnan(v)) or np.any(np.isinf(v)):
        return False
    if magnitude(v) < 1e-10:
        return False
    return True
