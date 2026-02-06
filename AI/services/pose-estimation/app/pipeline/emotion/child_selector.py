# app/pipeline/emotion/child_selector.py
"""
아이 얼굴 선택 모듈.

탐지된 얼굴 중 아이 얼굴을 Pose 정보 기반으로 선택합니다.
"""

import logging
import numpy as np
from typing import Optional

from .face_detector import FaceDetection

logger = logging.getLogger(__name__)


class ChildFaceSelector:
    """
    아이 얼굴 선택기.
    
    Pose 분석에서 얻은 아이의 머리 위치 정보를 활용하여
    탐지된 얼굴 중 아이 얼굴을 선택합니다.
    """
    
    def __init__(self, distance_threshold: float = 100.0):
        """
        ChildFaceSelector 초기화.
        
        Args:
            distance_threshold: 머리 위치와 얼굴 중심 간 최대 허용 거리 (픽셀)
        """
        self.distance_threshold = distance_threshold
        logger.info(f"ChildFaceSelector 초기화: distance_threshold={distance_threshold}")
    
    def select(
        self,
        faces: list[FaceDetection],
        child_head_pos: Optional[tuple[float, float]] = None,
        parent_head_pos: Optional[tuple[float, float]] = None
    ) -> Optional[FaceDetection]:
        """
        아이 얼굴 선택.
        
        선택 우선순위:
        1. Pose 기반 매칭 (child_head_pos가 주어진 경우)
        2. 크기 기반 휴리스틱 (얼굴 크기가 작은 쪽)
        3. 위치 기반 휴리스틱 (영상 하단에 위치한 쪽)
        
        Args:
            faces: 탐지된 얼굴 목록
            child_head_pos: 아이 머리 위치 (x, y) - Pose에서 추출
            parent_head_pos: 부모 머리 위치 (x, y) - 제외용
            
        Returns:
            아이 얼굴 또는 None
        """
        if not faces:
            return None
        
        if len(faces) == 1:
            # 얼굴이 하나면 그것이 아이라고 가정
            return faces[0]
        
        # 1. Pose 기반 매칭 시도
        if child_head_pos is not None:
            matched = self._match_by_pose(faces, child_head_pos)
            if matched:
                logger.debug("Pose 기반으로 아이 얼굴 선택됨")
                return matched
        
        # 2. 부모 위치 제외 후 선택
        if parent_head_pos is not None:
            remaining = self._exclude_parent(faces, parent_head_pos)
            if len(remaining) == 1:
                logger.debug("부모 제외 후 아이 얼굴 선택됨")
                return remaining[0]
            if remaining:
                faces = remaining
        
        # 3. 크기 기반 휴리스틱 (더 작은 얼굴 = 아이)
        child_face = self._select_by_size(faces)
        logger.debug("크기 기반으로 아이 얼굴 선택됨")
        return child_face
    
    def _match_by_pose(
        self,
        faces: list[FaceDetection],
        head_pos: tuple[float, float]
    ) -> Optional[FaceDetection]:
        """
        Pose 머리 위치와 가장 가까운 얼굴 매칭.
        
        Args:
            faces: 얼굴 목록
            head_pos: 머리 위치 (x, y)
            
        Returns:
            매칭된 얼굴 또는 None
        """
        best_face = None
        best_distance = float('inf')
        
        for face in faces:
            face_center = face.center
            distance = np.sqrt(
                (face_center[0] - head_pos[0]) ** 2 +
                (face_center[1] - head_pos[1]) ** 2
            )
            
            if distance < best_distance and distance < self.distance_threshold:
                best_distance = distance
                best_face = face
        
        return best_face
    
    def _exclude_parent(
        self,
        faces: list[FaceDetection],
        parent_head_pos: tuple[float, float]
    ) -> list[FaceDetection]:
        """
        부모 얼굴 제외.
        
        Args:
            faces: 얼굴 목록
            parent_head_pos: 부모 머리 위치
            
        Returns:
            부모 제외된 얼굴 목록
        """
        parent_face = self._match_by_pose(faces, parent_head_pos)
        if parent_face is None:
            return faces
        
        return [f for f in faces if f is not parent_face]
    
    def _select_by_size(self, faces: list[FaceDetection]) -> FaceDetection:
        """
        크기가 가장 작은 얼굴 선택 (아이 추정).
        
        Args:
            faces: 얼굴 목록
            
        Returns:
            가장 작은 얼굴
        """
        return min(faces, key=lambda f: f.area)
    
    def get_head_position_from_pose(
        self,
        keypoints: np.ndarray,
        frame_shape: tuple[int, int]
    ) -> Optional[tuple[float, float]]:
        """
        Pose 키포인트에서 머리 위치 추출.
        
        COCO 형식 키포인트에서 머리 중심을 계산합니다.
        (코, 눈, 귀 키포인트 평균)
        
        Args:
            keypoints: (17, 3) 형태의 키포인트 배열
            frame_shape: (height, width) 프레임 크기
            
        Returns:
            머리 중심 위치 (x, y) 또는 None
        """
        # COCO 키포인트: 0=Nose, 1=L_Eye, 2=R_Eye, 3=L_Ear, 4=R_Ear
        head_indices = [0, 1, 2, 3, 4]
        
        valid_points = []
        for idx in head_indices:
            if keypoints[idx, 2] > 0.3:  # confidence threshold
                # 정규화 좌표를 픽셀 좌표로 변환
                x = keypoints[idx, 0] * frame_shape[1]
                y = keypoints[idx, 1] * frame_shape[0]
                valid_points.append((x, y))
        
        if not valid_points:
            return None
        
        # 평균 위치 계산
        avg_x = sum(p[0] for p in valid_points) / len(valid_points)
        avg_y = sum(p[1] for p in valid_points) / len(valid_points)
        
        return (avg_x, avg_y)
