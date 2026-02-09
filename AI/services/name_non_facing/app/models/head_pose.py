# services/name_non_facing/app/models/head_pose.py
"""
Head Pose 추정 및 시선 벡터 생성

얼굴 랜드마크를 기반으로 머리 방향(Yaw, Pitch, Roll)과
시선 벡터를 계산합니다.

설계 의도:
    1. 귀-코 기반 시선 벡터 (정의에 따름)
       - 양쪽 귀를 잇는 축에 직교하고 코를 통과하는 벡터
       
    2. PnP 기반 Euler Angles (보조)
       - Yaw, Pitch, Roll 정밀 측정
       
    3. 위치 벡터와 비교 가능한 3D 벡터 출력

수학적 배경:
    시선 벡터 = normalize(ear_axis × up_vector)
    
    여기서:
    - ear_axis = P_right_ear - P_left_ear
    - up_vector = [0, -1, 0] (이미지 좌표계)
    - × = 외적 (cross product)

Reference:
    - Head Pose Estimation with OpenCV:
      https://learnopencv.com/head-pose-estimation-using-opencv-and-dlib/
    - solvePnP:
      https://docs.opencv.org/4.x/d5/d1f/calib3d_solvePnP.html
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import logging

import cv2
import numpy as np

from app.models.face_mesh import FaceLandmarks, LandmarkIndex
from app.core.vector_math import (
    normalize, cross, compute_gaze_vector_from_ears_nose
)

logger = logging.getLogger(__name__)


# 3D 얼굴 모델 포인트 (일반적인 얼굴 비율 기준)
# 단위: 임의 (상대적 비율)
FACE_3D_MODEL_POINTS = np.array([
    [0.0, 0.0, 0.0],          # Nose tip (1)
    [-30.0, -30.0, -30.0],    # Left eye outer (33)
    [30.0, -30.0, -30.0],     # Right eye outer (263)
    [-25.0, 30.0, -15.0],     # Mouth left (61)
    [25.0, 30.0, -15.0],      # Mouth right (291)
    [0.0, 50.0, -10.0],       # Chin (199)
], dtype=np.float64)


@dataclass
class HeadPose:
    """머리 자세 추정 결과"""
    yaw_deg: float              # 좌우 회전 (도)
    pitch_deg: float            # 상하 회전 (도)
    roll_deg: float             # 기울임 (도)
    gaze_vector: np.ndarray     # 시선 방향 단위 벡터 [x, y, z]
    nose_direction: np.ndarray  # 코 방향 벡터 (PnP 기반)
    
    @property
    def is_looking_forward(self) -> bool:
        """정면을 보고 있는지 (대략적)"""
        return abs(self.yaw_deg) < 30 and abs(self.pitch_deg) < 30
    
    @property
    def is_looking_left(self) -> bool:
        """왼쪽을 보고 있는지"""
        return self.yaw_deg < -15
    
    @property
    def is_looking_right(self) -> bool:
        """오른쪽을 보고 있는지"""
        return self.yaw_deg > 15
    
    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            "yaw_deg": self.yaw_deg,
            "pitch_deg": self.pitch_deg,
            "roll_deg": self.roll_deg,
            "gaze_vector": self.gaze_vector.tolist(),
            "nose_direction": self.nose_direction.tolist()
        }


class HeadPoseEstimator:
    """
    Head Pose 추정기
    
    Usage:
        estimator = HeadPoseEstimator(frame_width, frame_height)
        pose = estimator.estimate(landmarks)
        print(f"Yaw: {pose.yaw_deg}°, Gaze: {pose.gaze_vector}")
    """
    
    def __init__(self, frame_width: int, frame_height: int):
        """
        Args:
            frame_width: 프레임 너비 (픽셀)
            frame_height: 프레임 높이 (픽셀)
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # 카메라 매트릭스 (가상 카메라)
        focal_length = frame_width
        center = (frame_width / 2, frame_height / 2)
        
        self.camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        
        # 왜곡 계수 (없음 가정)
        self.dist_coeffs = np.zeros((4, 1))
    
    def estimate(self, landmarks: FaceLandmarks) -> HeadPose:
        """
        랜드마크에서 Head Pose 추정
        
        Args:
            landmarks: 얼굴 랜드마크
            
        Returns:
            HeadPose 결과
        """
        # 1. 귀-코 기반 시선 벡터 (정의에 따름)
        gaze_vector = compute_gaze_vector_from_ears_nose(
            left_ear=landmarks.left_ear,
            right_ear=landmarks.right_ear,
            nose_tip=landmarks.nose_tip
        )
        
        # 2. PnP 기반 Euler Angles
        yaw, pitch, roll, nose_direction = self._estimate_euler_angles(landmarks)
        
        return HeadPose(
            yaw_deg=yaw,
            pitch_deg=pitch,
            roll_deg=roll,
            gaze_vector=gaze_vector,
            nose_direction=nose_direction
        )
    
    def _estimate_euler_angles(
        self,
        landmarks: FaceLandmarks
    ) -> Tuple[float, float, float, np.ndarray]:
        """
        PnP 알고리즘으로 Euler Angles 추정
        
        Args:
            landmarks: 얼굴 랜드마크
            
        Returns:
            (yaw_deg, pitch_deg, roll_deg, nose_direction)
        """
        # 2D 이미지 포인트 (픽셀 좌표)
        pose_indices = LandmarkIndex.POSE_POINTS
        image_points = np.array([
            [
                landmarks.landmarks[idx][0] * self.frame_width,
                landmarks.landmarks[idx][1] * self.frame_height
            ]
            for idx in pose_indices
        ], dtype=np.float64)
        
        # solvePnP로 회전/이동 벡터 계산
        success, rotation_vector, translation_vector = cv2.solvePnP(
            FACE_3D_MODEL_POINTS,
            image_points,
            self.camera_matrix,
            self.dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            logger.warning("solvePnP 실패, 기본값 반환")
            return 0.0, 0.0, 0.0, np.array([0.0, 0.0, -1.0])
        
        # 회전 벡터 → 회전 행렬
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        
        # 회전 행렬 → Euler Angles
        # decomposition 사용
        proj_matrix = np.hstack((rotation_matrix, translation_vector))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(
            np.vstack((proj_matrix, [0, 0, 0, 1]))[:3]
        )
        
        pitch = float(euler_angles[0][0])
        yaw = float(euler_angles[1][0])
        roll = float(euler_angles[2][0])
        
        # 코 방향 벡터 (정면 방향을 회전)
        forward = np.array([0.0, 0.0, -1.0])
        nose_direction = rotation_matrix @ forward
        nose_direction = normalize(nose_direction)
        
        return yaw, pitch, roll, nose_direction
    
    def estimate_simple(self, landmarks: FaceLandmarks) -> HeadPose:
        """
        간단한 Head Pose 추정 (귀-코 기반만)
        
        PnP 없이 빠르게 시선 벡터만 계산합니다.
        
        Args:
            landmarks: 얼굴 랜드마크
            
        Returns:
            HeadPose (yaw/pitch는 근사값)
        """
        # 시선 벡터
        gaze_vector = compute_gaze_vector_from_ears_nose(
            left_ear=landmarks.left_ear,
            right_ear=landmarks.right_ear,
            nose_tip=landmarks.nose_tip
        )
        
        # 귀 축에서 yaw 근사 계산
        ear_axis = landmarks.right_ear - landmarks.left_ear
        
        # yaw: 귀 축이 x축과 이루는 각도
        yaw_rad = np.arctan2(ear_axis[2], ear_axis[0])
        yaw_deg = float(np.degrees(yaw_rad))
        
        # pitch: 시선 벡터의 y 성분
        pitch_rad = np.arcsin(-gaze_vector[1])
        pitch_deg = float(np.degrees(pitch_rad))
        
        # roll: 귀 축이 수평과 이루는 각도
        roll_rad = np.arctan2(ear_axis[1], ear_axis[0])
        roll_deg = float(np.degrees(roll_rad))
        
        return HeadPose(
            yaw_deg=yaw_deg,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
            gaze_vector=gaze_vector,
            nose_direction=gaze_vector  # 동일하게 사용
        )


def compute_gaze_to_target_angle(
    gaze_vector: np.ndarray,
    target_direction: np.ndarray
) -> float:
    """
    시선 벡터와 타겟 방향 사이의 각도 계산
    
    Args:
        gaze_vector: 시선 방향 단위 벡터
        target_direction: 타겟 방향 단위 벡터 (예: 부모 방향)
        
    Returns:
        각도 (도)
    """
    from app.core.angle_calculator import angle_between_vectors_deg
    return angle_between_vectors_deg(gaze_vector, target_direction)
