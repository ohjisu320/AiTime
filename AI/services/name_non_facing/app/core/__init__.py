# services/name_non_facing/app/core/__init__.py
"""
Core 모듈

분석 로직 및 계산 유틸리티를 제공합니다.

Modules:
    - gaze_calculator: Euler → 시선 벡터 변환, 각도 계산
    - angle_calculator: 각도 관련 계산 (deprecated)
    - vector_math: 벡터 연산
    - latency_tracker: 반응 지연 시간 추적
    - trial_manager: 시행 관리
"""

from app.core.gaze_calculator import (
    euler_to_gaze_vector,
    compute_position_vector_2d,
    angle_between_vectors,
    compute_gaze_angle,
    analyze_gaze,
    find_reaction_start_frame,
    GazeAnalysisResult,
)

__all__ = [
    # Gaze Calculator
    "euler_to_gaze_vector",
    "compute_position_vector_2d",
    "angle_between_vectors",
    "compute_gaze_angle",
    "analyze_gaze",
    "find_reaction_start_frame",
    "GazeAnalysisResult",
]
