# services/name_non_facing/app/models/face_detector.py
"""
MediaPipe Face Detection 래퍼 (Tasks API 버전)

비디오 프레임에서 얼굴을 탐지하고 바운딩박스를 반환합니다.

설계 의도:
    1. BaseModel 상속으로 싱글톤 + Lazy Loading
    2. 부모/아이 구분 로직 포함
    3. 1인칭 모드 지원 (부모 미탐지 시 카메라 중앙)

Reference:
    - MediaPipe Face Detection (Tasks API):
      https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import logging
import urllib.request

import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

from app.models.base import BaseModel
from app.config import get_settings

logger = logging.getLogger(__name__)

# 모델 파일 URL 및 경로 (full_range = 5m까지 탐지, 더 작은 얼굴도 OK)
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
MODEL_CACHE_DIR = Path.home() / ".cache" / "mediapipe"
MODEL_PATH = MODEL_CACHE_DIR / "blaze_face_short_range.tflite"


def download_model_if_needed():
    """모델 파일 다운로드 (없으면)"""
    if MODEL_PATH.exists():
        return str(MODEL_PATH)
    
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"🔽 모델 다운로드 중: {MODEL_URL}")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    logger.info(f"✅ 모델 다운로드 완료: {MODEL_PATH}")
    return str(MODEL_PATH)


@dataclass
class BoundingBox:
    """얼굴 바운딩박스"""
    x: float        # 좌상단 x (정규화 0~1)
    y: float        # 좌상단 y (정규화 0~1)
    width: float    # 너비 (정규화 0~1)
    height: float   # 높이 (정규화 0~1)
    
    @property
    def area(self) -> float:
        """면적 (정규화)"""
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        """중심점 (정규화)"""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def to_pixel(self, frame_width: int, frame_height: int) -> "BoundingBox":
        """픽셀 좌표로 변환"""
        return BoundingBox(
            x=self.x * frame_width,
            y=self.y * frame_height,
            width=self.width * frame_width,
            height=self.height * frame_height
        )
    
    def center_pixel(self, frame_width: int, frame_height: int) -> Tuple[float, float]:
        """중심점 (픽셀 좌표)"""
        cx = (self.x + self.width / 2) * frame_width
        cy = (self.y + self.height / 2) * frame_height
        return (cx, cy)


@dataclass
class FaceDetection:
    """얼굴 탐지 결과"""
    bbox: BoundingBox
    confidence: float
    person_type: str = "unknown"  # "parent", "child", "unknown"
    
    @property
    def center(self) -> Tuple[float, float]:
        """중심점 (정규화)"""
        return self.bbox.center
    
    def center_pixel(self, frame_width: int, frame_height: int) -> Tuple[float, float]:
        """중심점 (픽셀)"""
        return self.bbox.center_pixel(frame_width, frame_height)


class FaceDetector(BaseModel):
    """
    MediaPipe Face Detection 래퍼 (Tasks API)
    
    Usage:
        detector = FaceDetector()
        detections = detector.detect(frame)
        parent_pos, child = detector.identify_parent_child(detections, frame.shape)
    """
    
    def __init__(self):
        """FaceDetector 초기화"""
        # 싱글톤: 이미 초기화된 인스턴스면 skip (모델 재로딩 방지)
        if self._initialized:
            return
        self._settings = get_settings()
        self._detector = None
        self._initialized = True
    
    def _load_model(self) -> None:
        """MediaPipe Face Detection 모델 로드"""
        model_path = download_model_if_needed()
        
        base_options = BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=self._settings.FACE_DETECTION_CONFIDENCE,
            running_mode=vision.RunningMode.IMAGE
        )
        
        self._detector = vision.FaceDetector.create_from_options(options)
        
        logger.info(
            f"✅ FaceDetector 로드 완료 "
            f"(confidence={self._settings.FACE_DETECTION_CONFIDENCE})"
        )
    
    def ensure_loaded(self) -> None:
        """모델 로드 확인"""
        if not self._model_loaded:
            self._load_model()
            self._model_loaded = True
    
    def detect(self, frame: np.ndarray) -> List[FaceDetection]:
        """
        프레임에서 얼굴 탐지
        
        Args:
            frame: BGR 이미지 (OpenCV 형식)
            
        Returns:
            FaceDetection 목록
        """
        self.ensure_loaded()
        
        # BGR → RGB 변환
        rgb_frame = frame[:, :, ::-1].copy()
        
        # MediaPipe Image로 변환
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # 탐지 수행
        result = self._detector.detect(mp_image)
        
        frame_height, frame_width = frame.shape[:2]
        detections = []
        
        if result.detections:
            for detection in result.detections:
                bbox_data = detection.bounding_box
                
                # Tasks API는 픽셀 좌표 반환 → 정규화
                x = bbox_data.origin_x / frame_width
                y = bbox_data.origin_y / frame_height
                w = bbox_data.width / frame_width
                h = bbox_data.height / frame_height
                
                # 유효성 검사
                x = max(0.0, min(x, 1.0))
                y = max(0.0, min(y, 1.0))
                w = min(w, 1.0 - x)
                h = min(h, 1.0 - y)
                
                bbox = BoundingBox(x=x, y=y, width=w, height=h)
                confidence = detection.categories[0].score if detection.categories else 0.5
                
                detections.append(FaceDetection(
                    bbox=bbox,
                    confidence=confidence
                ))
        
        return detections
    
    def identify_parent_child(
        self,
        detections: List[FaceDetection],
        frame_shape: Tuple[int, int, int]
    ) -> Tuple[Tuple[float, float], Optional[FaceDetection]]:
        """
        부모/아이 구분
        
        전략:
        1. 얼굴 0개: 부모 = 프레임 중앙, 아이 = None
        2. 얼굴 1개: 부모 = 프레임 중앙 (1인칭), 아이 = 탐지된 얼굴
        3. 얼굴 2개+: bbox 크기가 큰 쪽 = 부모 (카메라에 가까움)
        
        Args:
            detections: 얼굴 탐지 목록
            frame_shape: (height, width, channels)
            
        Returns:
            (parent_center_pixel, child_detection)
            - parent_center_pixel: 부모 얼굴 중심 또는 프레임 중앙 (픽셀)
            - child_detection: 아이 FaceDetection 또는 None
        """
        height, width = frame_shape[:2]
        frame_center = (width / 2, height / 2)
        
        if len(detections) == 0:
            # 얼굴 없음 → 부모 = 중앙, 아이 = None
            logger.debug("얼굴 미탐지: 1인칭 모드 (아이 없음)")
            return frame_center, None
        
        if len(detections) == 1:
            # 1명만 탐지 → 1인칭 모드 (탐지된 얼굴 = 아이)
            child = detections[0]
            child.person_type = "child"
            logger.debug("1명 탐지: 1인칭 모드 (부모=중앙)")
            return frame_center, child
        
        # 2명 이상: 크기 기준 정렬 (큰 순)
        sorted_by_size = sorted(
            detections,
            key=lambda d: d.bbox.area,
            reverse=True
        )
        
        # 가장 큰 것 = 부모 (카메라에 가까움)
        parent = sorted_by_size[0]
        parent.person_type = "parent"
        parent_center = parent.center_pixel(width, height)
        
        # 두 번째 = 아이
        child = sorted_by_size[1]
        child.person_type = "child"
        
        logger.debug(
            f"2명 탐지: 부모 bbox={parent.bbox.area:.3f}, "
            f"아이 bbox={child.bbox.area:.3f}"
        )
        
        return parent_center, child
    
    def predict(self, frame: np.ndarray) -> List[FaceDetection]:
        """BaseModel 인터페이스 호환용"""
        return self.detect(frame)
    
    def close(self) -> None:
        """리소스 정리"""
        if self._detector is not None:
            self._detector.close()
            self._detector = None
        self._model_loaded = False
        logger.info("FaceDetector 종료")
    
    def unload(self) -> None:
        """모델 언로드 (close alias)"""
        self.close()
    
    def __del__(self):
        """소멸자"""
        try:
            self.close()
        except:
            pass
