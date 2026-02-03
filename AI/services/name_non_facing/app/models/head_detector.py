# services/name_non_facing/app/models/head_detector.py
"""
YOLO Head Detector 래퍼

YOLOv8 Head-specific 모델을 사용하여 머리를 직접 탐지합니다.
(Person detection 후 추정 로직 제거 - 단순화)

설계 의도:
    1. Head-specific YOLO 모델로 직접 머리 탐지 (360° 뒤통수 포함)
    2. 부모/아이 구분 (점수 기반: 위치 + 크기 + 중앙 근접도)
    3. 1인칭 모드 지원 (부모 미탐지 시 카메라 중앙)

Fine-tuning:
    - Kaggle Human Head Detection 데이터셋 사용
    - https://www.kaggle.com/datasets/hoangxuanviet/human-head-detection-openvm-c270
    - 모델: yolov8-head.pt (head class만 탐지)

Reference:
    - Ultralytics YOLOv8: https://docs.ultralytics.com/
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import logging

import numpy as np

from app.models.base import BaseModel
from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """머리 바운딩박스"""
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
    
    def to_xyxy_pixel(self, frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """(x1, y1, x2, y2) 픽셀 좌표로 변환"""
        x1 = int(self.x * frame_width)
        y1 = int(self.y * frame_height)
        x2 = int((self.x + self.width) * frame_width)
        y2 = int((self.y + self.height) * frame_height)
        return (x1, y1, x2, y2)


@dataclass
class HeadDetection:
    """머리 탐지 결과"""
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


class HeadDetector(BaseModel):
    """
    YOLO Head Detector (Head-specific 모델 전용)
    
    Fine-tuned YOLOv8 모델을 사용하여 머리를 직접 탐지합니다.
    - Person detection 후 추정 로직 제거 (단순화)
    - Head class만 탐지하므로 더 정확
    - 뒤통수 포함 360° 탐지 가능
    
    Usage:
        detector = HeadDetector()
        detections = detector.detect(frame)
        parent_pos, child = detector.identify_parent_child(detections, frame.shape)
    """
    
    def __init__(self, model_path: str = None):
        """
        HeadDetector 초기화
        
        Args:
            model_path: YOLO 모델 경로 (None이면 config에서 가져옴)
        """
        self._settings = get_settings()
        self._model_path = model_path or self._settings.YOLO_HEAD_MODEL
        self._model = None
        self._model_loaded = False
    
    def _load_model(self) -> None:
        """YOLO 모델 로드"""
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics 패키지가 필요합니다. "
                "pip install ultralytics 로 설치하세요."
            )
        
        logger.info(f"🔽 YOLO 모델 로드 중: {self._model_path}")
        self._model = YOLO(self._model_path)
        
        logger.info(
            f"✅ HeadDetector 로드 완료 "
            f"(model={self._model_path}, confidence={self._settings.YOLO_HEAD_CONFIDENCE})"
        )
    
    def ensure_loaded(self) -> None:
        """모델 로드 확인"""
        if not self._model_loaded:
            self._load_model()
            self._model_loaded = True
    
    def detect(self, frame: np.ndarray) -> List[HeadDetection]:
        """
        프레임에서 머리 탐지 (Head-specific 모델 직접 탐지)
        
        Args:
            frame: BGR 이미지 (OpenCV 형식)
            
        Returns:
            HeadDetection 목록
        """
        self.ensure_loaded()
        
        frame_height, frame_width = frame.shape[:2]
        
        # YOLO 추론 (head class만 탐지)
        results = self._model(
            frame,
            conf=self._settings.YOLO_HEAD_CONFIDENCE,
            verbose=False
        )
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            
            if boxes is None or len(boxes) == 0:
                continue
            
            for i in range(len(boxes)):
                # bbox 좌표 (xyxy 형식, 픽셀)
                xyxy = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                
                # 정규화 (0~1)
                x = x1 / frame_width
                y = y1 / frame_height
                w = (x2 - x1) / frame_width
                h = (y2 - y1) / frame_height
                
                # 유효성 검사
                x = max(0.0, min(x, 1.0))
                y = max(0.0, min(y, 1.0))
                w = min(w, 1.0 - x)
                h = min(h, 1.0 - y)
                
                confidence = float(boxes.conf[i].cpu().numpy())
                
                # Head bbox 생성 (추정 로직 없이 직접 사용)
                head_bbox = BoundingBox(x=x, y=y, width=w, height=h)
                
                detections.append(HeadDetection(
                    bbox=head_bbox,
                    confidence=confidence
                ))
        
        return detections
    
    def identify_parent_child(
        self,
        detections: List[HeadDetection],
        frame_shape: Tuple[int, int, int]
    ) -> Tuple[Tuple[float, float], Optional[HeadDetection]]:
        """
        부모/아이 구분 (점수 기반)
        
        전략:
        1. 머리 0개: 부모 = 프레임 중앙, 아이 = None
        2. 머리 1개: 부모 = 프레임 중앙 (1인칭), 아이 = 탐지된 머리
        3. 머리 2개+: 점수 기반 판별
           - Y 위치 (하단 = 아이)
           - 크기 (작은 것 = 아이)
           - 중앙 근접도 (멀수록 = 아이)
        
        Args:
            detections: 머리 탐지 목록
            frame_shape: (height, width, channels)
            
        Returns:
            (parent_center_pixel, child_detection)
            - parent_center_pixel: 부모 머리 중심 또는 프레임 중앙 (픽셀)
            - child_detection: 아이 HeadDetection 또는 None
        """
        height, width = frame_shape[:2]
        frame_center = (width / 2, height / 2)
        
        if len(detections) == 0:
            # 머리 미탐지
            logger.debug("머리 미탐지: 1인칭 모드 (아이 없음)")
            return frame_center, None
        
        if len(detections) == 1:
            # 1명만 탐지 → 1인칭 모드 (탐지된 머리 = 아이)
            child = detections[0]
            child.person_type = "child"
            logger.debug("1명 탐지: 1인칭 모드 (부모=중앙)")
            return frame_center, child
        
        # 2명 이상: 점수 기반 판별
        frame_center_x = 0.5
        frame_center_y = 0.5
        
        scores = []
        for det in detections:
            cx, cy = det.bbox.center
            
            # 아이 점수 계산 (높을수록 아이일 가능성)
            y_score = cy  # Y 위치 (아래쪽 = 높음)
            size_score = 1.0 - det.bbox.area  # 크기 (작을수록 = 높음)
            dist_to_center = np.sqrt((cx - frame_center_x)**2 + (cy - frame_center_y)**2)
            
            # 가중치: Y 위치 > 크기 > 중앙 거리
            child_score = (
                y_score * 2.5 +
                size_score * 1.5 +
                dist_to_center * 0.8
            )
            
            scores.append((det, child_score))
        
        # 가장 높은 점수 = 아이, 가장 낮은 점수 = 부모
        scores.sort(key=lambda x: x[1], reverse=True)
        child = scores[0][0]
        child.person_type = "child"
        
        if len(scores) > 1:
            parent = scores[-1][0]
            parent.person_type = "parent"
            parent_center = parent.center_pixel(width, height)
        else:
            parent_center = frame_center
        
        return parent_center, child
    
    def predict(self, frame: np.ndarray) -> List[HeadDetection]:
        """BaseModel 인터페이스 호환용"""
        return self.detect(frame)
    
    def close(self) -> None:
        """리소스 정리"""
        if self._model is not None:
            del self._model
            self._model = None
        self._model_loaded = False
        logger.info("HeadDetector 종료")
    
    def unload(self) -> None:
        """모델 언로드 (close alias)"""
        self.close()
    
    def __del__(self):
        """소멸자"""
        try:
            self.close()
        except Exception:
            pass
