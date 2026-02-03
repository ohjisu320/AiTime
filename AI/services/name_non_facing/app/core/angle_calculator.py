# services/name_non_facing/app/core/angle_calculator.py
"""
벡터 간 각도 계산 유틸리티

두 벡터 사이의 3D 공간 각도를 계산합니다.
시선 벡터와 위치 벡터 간의 각도 비교에 사용됩니다.

설계 의도:
    1. 3D 공간 각도 정확 계산
       - arccos 기반 각도 계산
       - 부동소수점 오차 처리
       
    2. 임계치 비교 기능
       - 반응 성공 여부 판정에 직접 사용

수학적 배경:
    두 단위 벡터 v1, v2 사이의 각도 θ:
    
    cos(θ) = v1 · v2  (내적)
    θ = arccos(v1 · v2)
    
    ※ 단위 벡터가 아닌 경우:
    cos(θ) = (v1 · v2) / (|v1| × |v2|)

Reference:
    - 벡터 각도: https://en.wikipedia.org/wiki/Dot_product#Geometric_definition
"""

import numpy as np

from app.core.vector_math import normalize, dot, magnitude, is_valid_vector


def angle_between_vectors_rad(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    두 벡터 사이의 각도 (라디안)
    
    Args:
        v1, v2: 입력 벡터 (2D 또는 3D)
        
    Returns:
        각도 (라디안, 0 ~ π)
        
    수학적 정의:
        θ = arccos((v1 · v2) / (|v1| × |v2|))
        
    Note:
        - 영벡터 입력 시 π (180°) 반환
        - 부동소수점 오차로 |cos| > 1 가능 → clamp 처리
    """
    # 유효성 검사
    if not is_valid_vector(v1) or not is_valid_vector(v2):
        return np.pi  # 유효하지 않으면 최대 각도
    
    # 정규화
    v1_norm = normalize(v1)
    v2_norm = normalize(v2)
    
    # 내적 계산
    cos_theta = dot(v1_norm, v2_norm)
    
    # 부동소수점 오차 처리 (clamp to [-1, 1])
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
    # 각도 계산
    angle_rad = np.arccos(cos_theta)
    
    return float(angle_rad)


def angle_between_vectors_deg(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    두 벡터 사이의 각도 (도, degree)
    
    Args:
        v1, v2: 입력 벡터 (2D 또는 3D)
        
    Returns:
        각도 (도, 0° ~ 180°)
    """
    angle_rad = angle_between_vectors_rad(v1, v2)
    return float(np.degrees(angle_rad))


def is_within_threshold(
    v1: np.ndarray,
    v2: np.ndarray,
    threshold_deg: float
) -> bool:
    """
    두 벡터의 각도가 임계치 이내인지 확인
    
    Args:
        v1, v2: 입력 벡터
        threshold_deg: 임계치 (도)
        
    Returns:
        임계치 이내 여부
        
    Usage:
        # 시선이 부모 방향을 향하고 있는지 확인 (20° 이내)
        is_looking = is_within_threshold(gaze_vec, position_vec, 20.0)
    """
    angle_deg = angle_between_vectors_deg(v1, v2)
    return angle_deg <= threshold_deg


def signed_angle_2d_deg(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    2D 벡터의 부호 있는 각도 (v1 → v2 방향)
    
    Args:
        v1, v2: 2D 벡터
        
    Returns:
        부호 있는 각도 (도, -180° ~ 180°)
        양수: 반시계 방향
        음수: 시계 방향
        
    Note:
        고개 회전 방향 분석에 유용
    """
    if len(v1) != 2 or len(v2) != 2:
        raise ValueError("2D 벡터만 지원합니다")
    
    # atan2로 각 벡터의 방향각 계산
    angle1 = np.arctan2(v1[1], v1[0])
    angle2 = np.arctan2(v2[1], v2[0])
    
    # 차이 계산
    diff = angle2 - angle1
    
    # -π ~ π 범위로 정규화
    while diff > np.pi:
        diff -= 2 * np.pi
    while diff < -np.pi:
        diff += 2 * np.pi
    
    return float(np.degrees(diff))


def angular_difference_sequence(angles: list) -> list:
    """
    각도 시퀀스의 변화량 계산
    
    Args:
        angles: 시간순 각도 목록 (도)
        
    Returns:
        각도 변화량 목록 (도)
        
    Usage:
        # 고개 회전 시작점 탐지
        angles = [45.2, 42.1, 35.0, 20.5, 18.3]  # 시간순
        diffs = angular_difference_sequence(angles)
        # → [-3.1, -7.1, -14.5, -2.2]  # 감소 = 부모 방향으로 돌림
    """
    if len(angles) < 2:
        return []
    
    diffs = []
    for i in range(1, len(angles)):
        diff = angles[i] - angles[i-1]
        diffs.append(diff)
    
    return diffs


def find_angle_crossing_index(
    angles: list,
    threshold_deg: float,
    direction: str = "below"
) -> int:
    """
    각도가 임계치를 처음 교차하는 인덱스 찾기
    
    Args:
        angles: 시간순 각도 목록 (도)
        threshold_deg: 임계치 (도)
        direction: "below" (임계치 이하로 진입) 또는 "above" (이상으로 벗어남)
        
    Returns:
        교차 인덱스 (-1이면 교차 없음)
        
    Usage:
        # 시선이 20° 이내로 처음 진입한 시점
        angles = [45.2, 35.0, 22.0, 18.5, 15.0]
        idx = find_angle_crossing_index(angles, 20.0, "below")
        # → 3 (18.5°에서 처음으로 20° 이하)
    """
    for i, angle in enumerate(angles):
        if direction == "below" and angle <= threshold_deg:
            return i
        elif direction == "above" and angle >= threshold_deg:
            return i
    return -1


def is_stable_below_threshold(
    angles: list,
    start_idx: int,
    threshold_deg: float,
    required_count: int
) -> bool:
    """
    특정 인덱스부터 임계치 이하 상태가 안정적으로 유지되는지 확인
    
    Args:
        angles: 시간순 각도 목록 (도)
        start_idx: 시작 인덱스
        threshold_deg: 임계치 (도)
        required_count: 필요한 연속 프레임 수
        
    Returns:
        안정 유지 여부
        
    Usage:
        # 20° 이하 상태가 3프레임 연속 유지되는지
        is_stable = is_stable_below_threshold(angles, 3, 20.0, 3)
    """
    if start_idx + required_count > len(angles):
        return False
    
    for i in range(required_count):
        if angles[start_idx + i] > threshold_deg:
            return False
    return True


def find_stable_crossing_index(
    angles: list,
    threshold_deg: float,
    stabilize_count: int = 3
) -> int:
    """
    임계치 이하로 "안정적으로" 진입한 시점의 인덱스 찾기
    
    Args:
        angles: 시간순 각도 목록 (도)
        threshold_deg: 임계치 (도)
        stabilize_count: 안정화 판정에 필요한 연속 프레임 수
        
    Returns:
        안정적 교차 시작 인덱스 (-1이면 없음)
        
    알고리즘:
        1. 임계치 이하인 구간 탐색
        2. 해당 구간이 stabilize_count 이상 연속되면 시작점 반환
        
    Usage:
        # T_react 계산: 20° 이하가 3프레임 연속 유지된 시작점
        angles = [45, 35, 22, 18, 19, 17, 16, 15]
        idx = find_stable_crossing_index(angles, 20.0, 3)
        # → 3 (18°부터 3프레임 연속 20° 이하)
    """
    for i in range(len(angles) - stabilize_count + 1):
        if is_stable_below_threshold(angles, i, threshold_deg, stabilize_count):
            return i
    return -1


def compute_gaze_statistics(angles: list) -> dict:
    """
    각도 시퀀스의 통계 정보 계산
    
    Args:
        angles: 각도 목록 (도)
        
    Returns:
        통계 딕셔너리:
        - min: 최소 각도
        - max: 최대 각도
        - mean: 평균 각도
        - std: 표준편차
        - range: 범위 (max - min)
    """
    if not angles:
        return {
            "min": None,
            "max": None,
            "mean": None,
            "std": None,
            "range": None
        }
    
    arr = np.array(angles)
    return {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "range": float(np.max(arr) - np.min(arr))
    }
