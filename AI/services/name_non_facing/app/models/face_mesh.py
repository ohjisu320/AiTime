# services/name_non_facing/app/models/face_mesh.py
"""
MediaPipe Face Mesh 래퍼 (Tasks API - FaceLandmarker)

얼굴에서 478개의 3D 랜드마크를 추출합니다.
시선 벡터 계산에 필요한 귀, 코 등의 좌표를 제공합니다.

설계 의도:
    1. 3D 랜드마크 추출 (x, y, z)
    2. 핵심 포인트 빠른 접근 (귀, 코 등)
    3. Head Pose 계산을 위한 데이터 제공

핵심 랜드마크 인덱스:
    - 코끝: 1
    - 왼쪽 귀 (tragion): 234
    - 오른쪽 귀 (tragion): 454

Reference:
    - MediaPipe Face Landmarker (Tasks API):
      https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List
import logging
import urllib.request

import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

from app.models.base import BaseModel
from app.config import get_settings

logger = logging.getLogger(__name__)

# 모델 파일 URL 및 경로
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
MODEL_CACHE_DIR = Path.home() / ".cache" / "mediapipe"
MODEL_PATH = MODEL_CACHE_DIR / "face_landmarker.task"


def download_model_if_needed():
    """모델 파일 다운로드 (없으면)"""
    if MODEL_PATH.exists():
        return str(MODEL_PATH)
    
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"🔽 FaceLandmarker 모델 다운로드 중: {MODEL_URL}")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    logger.info(f"✅ 모델 다운로드 완료: {MODEL_PATH}")
    return str(MODEL_PATH)


# 핵심 랜드마크 인덱스
class LandmarkIndex:
    """MediaPipe Face Mesh 랜드마크 인덱스"""
    NOSE_TIP = 1
    LEFT_EAR_TRAGION = 234
    RIGHT_EAR_TRAGION = 454
    
    # 눈 관련
    LEFT_EYE_INNER = 133
    LEFT_EYE_OUTER = 33
    RIGHT_EYE_INNER = 362
    RIGHT_EYE_OUTER = 263
    
    # 입 관련
    MOUTH_LEFT = 61
    MOUTH_RIGHT = 291
    UPPER_LIP = 0
    LOWER_LIP = 17
    
    # 얼굴 윤곽
    CHIN = 152
    FOREHEAD = 10
    LEFT_CHEEK = 234
    RIGHT_CHEEK = 454
    
    # Head Pose 추정용 6개 포인트
    POSE_POINTS = [1, 33, 263, 61, 291, 199]


@dataclass
class FaceLandmarks:
    """얼굴 랜드마크 결과"""
    landmarks: np.ndarray           # (478, 3) 정규화 좌표
    nose_tip: np.ndarray            # [x, y, z]
    left_ear: np.ndarray            # [x, y, z]
    right_ear: np.ndarray           # [x, y, z]
    confidence: float = 1.0
    
    # 3D 좌표 속성 (Tasks API는 x,y,z를 정규화 좌표로 반환)
    @property
    def nose_3d(self) -> np.ndarray:
        return self.nose_tip
    
    @property
    def left_ear_3d(self) -> np.ndarray:
        return self.left_ear
    
    @property
    def right_ear_3d(self) -> np.ndarray:
        return self.right_ear
    
    @property
    def ear_distance(self) -> float:
        """양쪽 귀 사이 거리 (정규화)"""
        return float(np.linalg.norm(self.right_ear - self.left_ear))
    
    @property
    def ear_midpoint(self) -> np.ndarray:
        """양쪽 귀 중점"""
        return (self.left_ear + self.right_ear) / 2
    
    def get_landmark(self, index: int) -> np.ndarray:
        """특정 인덱스의 랜드마크 반환"""
        return self.landmarks[index].copy()
    
    def get_pose_points(self) -> np.ndarray:
        """Head Pose 추정용 6개 포인트 반환"""
        indices = LandmarkIndex.POSE_POINTS
        return self.landmarks[indices].copy()
    
    def to_pixel_coords(
        self,
        frame_width: int,
        frame_height: int
    ) -> "FaceLandmarks":
        """픽셀 좌표로 변환 (z는 유지)"""
        pixel_landmarks = self.landmarks.copy()
        pixel_landmarks[:, 0] *= frame_width
        pixel_landmarks[:, 1] *= frame_height
        # z는 깊이 정보로 그대로 유지
        
        return FaceLandmarks(
            landmarks=pixel_landmarks,
            nose_tip=np.array([
                self.nose_tip[0] * frame_width,
                self.nose_tip[1] * frame_height,
                self.nose_tip[2]
            ]),
            left_ear=np.array([
                self.left_ear[0] * frame_width,
                self.left_ear[1] * frame_height,
                self.left_ear[2]
            ]),
            right_ear=np.array([
                self.right_ear[0] * frame_width,
                self.right_ear[1] * frame_height,
                self.right_ear[2]
            ]),
            confidence=self.confidence
        )


class FaceMesh(BaseModel):
    """
    MediaPipe FaceLandmarker 래퍼 (Tasks API)
    
    Usage:
        mesh = FaceMesh()
        landmarks = mesh.detect(frame)
        if landmarks:
            gaze = compute_gaze_vector(landmarks.left_ear, landmarks.right_ear, landmarks.nose_tip)
    """
    
    def __init__(self):
        """FaceMesh 초기화"""
        # 싱글톤: 이미 초기화된 인스턴스면 skip (모델 재로딩 방지)
        if self._initialized:
            return
        self._settings = get_settings()
        self._landmarker = None
        self._initialized = True
    
    def _load_model(self) -> None:
        """MediaPipe FaceLandmarker 모델 로드"""
        model_path = download_model_if_needed()
        
        base_options = BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=2,                # 최대 2명 (부모 + 아이)
            min_face_detection_confidence=self._settings.FACE_MESH_CONFIDENCE,
            min_face_presence_confidence=self._settings.FACE_MESH_CONFIDENCE,
            min_tracking_confidence=self._settings.FACE_MESH_CONFIDENCE,
            running_mode=vision.RunningMode.IMAGE
        )
        
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        
        logger.info(
            f"✅ FaceMesh (FaceLandmarker) 로드 완료 "
            f"(confidence={self._settings.FACE_MESH_CONFIDENCE})"
        )
    
    def ensure_loaded(self) -> None:
        """모델 로드 확인"""
        if not self._model_loaded:
            self._load_model()
            self._model_loaded = True
    
    def detect(
        self,
        frame: np.ndarray,
        face_index: int = 0
    ) -> Optional[FaceLandmarks]:
        """
        프레임에서 얼굴 랜드마크 추출
        
        Args:
            frame: BGR 이미지 (OpenCV 형식)
            face_index: 추출할 얼굴 인덱스 (0부터)
            
        Returns:
            FaceLandmarks 또는 None (탐지 실패 시)
        """
        self.ensure_loaded()
        
        # BGR → RGB 변환
        rgb_frame = frame[:, :, ::-1].copy()
        
        # MediaPipe Image로 변환
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # 랜드마크 추출
        result = self._landmarker.detect(mp_image)
        
        if not result.face_landmarks:
            return None
        
        if face_index >= len(result.face_landmarks):
            return None
        
        face_landmarks = result.face_landmarks[face_index]
        
        # 478개 랜드마크를 numpy 배열로 변환
        landmarks = np.array([
            [lm.x, lm.y, lm.z]
            for lm in face_landmarks
        ])
        
        # 핵심 포인트 추출
        nose_tip = landmarks[LandmarkIndex.NOSE_TIP].copy()
        left_ear = landmarks[LandmarkIndex.LEFT_EAR_TRAGION].copy()
        right_ear = landmarks[LandmarkIndex.RIGHT_EAR_TRAGION].copy()
        
        return FaceLandmarks(
            landmarks=landmarks,
            nose_tip=nose_tip,
            left_ear=left_ear,
            right_ear=right_ear
        )
    
    def extract(
        self,
        frame: np.ndarray,
        face_index: int = 0
    ) -> Optional[FaceLandmarks]:
        """detect()의 alias (호환성)"""
        return self.detect(frame, face_index)
    
    def extract_from_bbox(
        self,
        frame: np.ndarray,
        bbox_pixel: Tuple[float, float, float, float]
    ) -> Optional[FaceLandmarks]:
        """
        바운딩박스 영역에서 랜드마크 추출 (ROI 기반)
        
        Args:
            frame: BGR 이미지
            bbox_pixel: (x, y, width, height) 픽셀 좌표
            
        Returns:
            FaceLandmarks (원본 프레임 좌표계) 또는 None
            
        Note:
            - ROI를 잘라서 처리하면 정확도가 떨어질 수 있음
            - 전체 프레임에서 추출 후 bbox 내 얼굴 선택 권장
        """
        # 전체 프레임에서 추출
        all_landmarks = self.extract_all(frame)
        
        if not all_landmarks:
            return None
        
        x, y, w, h = bbox_pixel
        cx_target = x + w / 2
        cy_target = y + h / 2
        
        height, width = frame.shape[:2]
        
        # bbox 중심에 가장 가까운 얼굴 선택
        best_match = None
        min_distance = float('inf')
        
        for landmarks in all_landmarks:
            nose_pixel = landmarks.nose_tip.copy()
            nose_pixel[0] *= width
            nose_pixel[1] *= height
            
            distance = np.sqrt(
                (nose_pixel[0] - cx_target) ** 2 +
                (nose_pixel[1] - cy_target) ** 2
            )
            
            if distance < min_distance:
                min_distance = distance
                best_match = landmarks
        
        return best_match
    
    def extract_all(self, frame: np.ndarray) -> List[FaceLandmarks]:
        """
        프레임에서 모든 얼굴의 랜드마크 추출
        
        Args:
            frame: BGR 이미지
            
        Returns:
            FaceLandmarks 목록
        """
        self.ensure_loaded()
        
        rgb_frame = frame[:, :, ::-1].copy()
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        result = self._landmarker.detect(mp_image)
        
        if not result.face_landmarks:
            return []
        
        landmarks_list = []
        for face_landmarks in result.face_landmarks:
            landmarks = np.array([
                [lm.x, lm.y, lm.z]
                for lm in face_landmarks
            ])
            
            nose_tip = landmarks[LandmarkIndex.NOSE_TIP].copy()
            left_ear = landmarks[LandmarkIndex.LEFT_EAR_TRAGION].copy()
            right_ear = landmarks[LandmarkIndex.RIGHT_EAR_TRAGION].copy()
            
            landmarks_list.append(FaceLandmarks(
                landmarks=landmarks,
                nose_tip=nose_tip,
                left_ear=left_ear,
                right_ear=right_ear
            ))
        
        return landmarks_list
    
    def predict(self, frame: np.ndarray) -> Optional[FaceLandmarks]:
        """BaseModel 인터페이스 호환용"""
        return self.detect(frame)
    
    def close(self) -> None:
        """리소스 정리"""
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
        self._model_loaded = False
        logger.info("FaceMesh 종료")
    
    def unload(self) -> None:
        """모델 언로드 (close alias)"""
        self.close()
    
    def __del__(self):
        """소멸자"""
        try:
            self.close()
        except:
            pass
