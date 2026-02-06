# app/pipeline/emotion/face_detector.py
"""
얼굴 탐지 모듈.

RetinaFace를 사용하여 프레임에서 얼굴을 탐지합니다.
"""

import logging
import numpy as np
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# 얼굴 탐지기 지연 로딩
_detector = None
_detector_available = None


@dataclass
class FaceDetection:
    """
    얼굴 탐지 결과.
    
    Attributes:
        bbox: 바운딩 박스 (x1, y1, x2, y2)
        confidence: 탐지 신뢰도
        landmarks: 5개 랜드마크 좌표 (눈, 코, 입꼬리)
    """
    bbox: tuple[int, int, int, int]
    confidence: float
    landmarks: Optional[np.ndarray] = None
    
    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center(self) -> tuple[float, float]:
        """얼굴 중심 좌표"""
        return (
            (self.bbox[0] + self.bbox[2]) / 2,
            (self.bbox[1] + self.bbox[3]) / 2
        )


def _load_detector():
    """RetinaFace 탐지기 지연 로딩"""
    global _detector, _detector_available
    
    if _detector_available is not None:
        return _detector
    
    try:
        from retinaface import RetinaFaceDetector
        _detector = RetinaFaceDetector()
        _detector_available = True
        logger.info("✅ RetinaFace 로드 성공")
    except ImportError as e:
        logger.warning(f"⚠️ RetinaFace 없음 ({e}), OpenCV Haar Cascade로 폴백")
        _detector_available = False
        _detector = None
    except Exception as e:
        logger.warning(f"⚠️ RetinaFace 로드 실패 ({e}), OpenCV Haar Cascade로 폴백")
        _detector_available = False
        _detector = None
    
    return _detector


class FaceDetector:
    """
    얼굴 탐지기.
    
    RetinaFace를 사용하며, 없을 경우 OpenCV Haar Cascade로 폴백합니다.
    """
    
    def __init__(self, min_face_size: int = 40, confidence_threshold: float = 0.7):
        """
        FaceDetector 초기화.
        
        Args:
            min_face_size: 최소 얼굴 크기 (픽셀)
            confidence_threshold: 탐지 신뢰도 임계값
        """
        self.min_face_size = min_face_size
        self.confidence_threshold = confidence_threshold
        self._haar_cascade = None
        
        # 탐지기 초기화
        _load_detector()
        
        logger.info(
            f"FaceDetector 초기화: min_size={min_face_size}, confidence={confidence_threshold:.2f}, "
            f"backend={'RetinaFace' if _detector_available else 'Haar Cascade'}"
        )
    
    def detect(self, frame_bgr: np.ndarray) -> list[FaceDetection]:
        """
        프레임에서 얼굴 탐지.
        
        Args:
            frame_bgr: BGR 형식 프레임 (OpenCV 형식)
            
        Returns:
            탐지된 얼굴 목록
        """
        if _detector_available:
            return self._detect_retinaface(frame_bgr)
        else:
            return self._detect_haar(frame_bgr)
    
    def _detect_retinaface(self, frame_bgr: np.ndarray) -> list[FaceDetection]:
        """RetinaFace로 얼굴 탐지"""
        try:
            import cv2
            # BGR to RGB 변환
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
            # inference 메서드 사용
            # 반환 형식: {'bbox': [[x1, y1, x2, y2]], 'score': [confidence], 'landmarks': [5x2 array]}
            faces_dict = _detector.inference(frame_rgb)
            
            if faces_dict is None or 'bbox' not in faces_dict or len(faces_dict['bbox']) == 0:
                logger.debug("RetinaFace: 얼굴 미탐지")
                return []
            
            results = []
            bboxes = faces_dict['bbox']
            scores = faces_dict.get('score', [1.0] * len(bboxes))
            landmarks_list = faces_dict.get('landmarks', [None] * len(bboxes))
            
            for i, bbox in enumerate(bboxes):
                confidence = scores[i] if i < len(scores) else 1.0
                
                if confidence < self.confidence_threshold:
                    logger.debug(f"RetinaFace: 신뢰도 낮음 ({confidence:.2f} < {self.confidence_threshold:.2f})")
                    continue
                
                x1, y1, x2, y2 = bbox
                
                # 최소 크기 필터링
                face_width = x2 - x1
                face_height = y2 - y1
                if face_width < self.min_face_size or face_height < self.min_face_size:
                    logger.debug(f"RetinaFace: 얼굴 크기 작음 ({face_width}x{face_height} < {self.min_face_size})")
                    continue
                
                # 랜드마크 추출
                landmarks = landmarks_list[i] if i < len(landmarks_list) and landmarks_list[i] is not None else None
                if landmarks is not None and not isinstance(landmarks, np.ndarray):
                    landmarks = np.array(landmarks, dtype=np.float32)
                
                results.append(FaceDetection(
                    bbox=(int(x1), int(y1), int(x2), int(y2)),
                    confidence=float(confidence),
                    landmarks=landmarks
                ))
            
            
            logger.debug(f"RetinaFace: {len(results)}개 얼굴 탐지됨")
            return results
            
        except Exception as e:
            logger.warning(f"RetinaFace 탐지 실패: {e}, Haar로 폴백")
            return self._detect_haar(frame_bgr)
    
    def _detect_haar(self, frame_bgr: np.ndarray) -> list[FaceDetection]:
        """OpenCV Haar Cascade로 얼굴 탐지 (폴백)"""
        import cv2
        
        if self._haar_cascade is None:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._haar_cascade = cv2.CascadeClassifier(cascade_path)
        
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self._haar_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(self.min_face_size, self.min_face_size)
        )
        
        results = []
        for (x, y, w, h) in faces:
            results.append(FaceDetection(
                bbox=(int(x), int(y), int(x + w), int(y + h)),
                confidence=1.0,  # Haar는 confidence 미제공
                landmarks=None
            ))
        
        return results
    
    def crop_face(
        self,
        frame_bgr: np.ndarray,
        face: FaceDetection,
        margin: float = 0.1
    ) -> np.ndarray:
        """
        얼굴 영역 크롭.
        
        Args:
            frame_bgr: 원본 프레임
            face: 얼굴 탐지 결과
            margin: 마진 비율 (0.1 = 10%)
            
        Returns:
            크롭된 얼굴 이미지
        """
        h, w = frame_bgr.shape[:2]
        x1, y1, x2, y2 = face.bbox
        
        # 마진 추가
        margin_w = int((x2 - x1) * margin)
        margin_h = int((y2 - y1) * margin)
        
        x1 = max(0, x1 - margin_w)
        y1 = max(0, y1 - margin_h)
        x2 = min(w, x2 + margin_w)
        y2 = min(h, y2 + margin_h)
        
        return frame_bgr[y1:y2, x1:x2].copy()
