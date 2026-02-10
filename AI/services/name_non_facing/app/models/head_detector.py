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
import cv2

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
    track_id: Optional[int] = None  # YOLO tracking ID
    
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
        # 싱글톤: 이미 초기화된 인스턴스면 skip (모델 재로딩 방지)
        if self._initialized:
            return
        self._settings = get_settings()
        self._model_path = model_path or self._settings.YOLO_HEAD_MODEL
        
        # HeadDetector 전용 인스턴스 변수 초기화
        self._face_detector = None  # MediaPipe Face Detection
        self._face_detector_loaded = False
        
        # Smoothing state (track_id별로 이전 값 저장)
        self._smoothing_state: dict[int, dict] = {}  # {track_id: {bbox, pose, gaze, ...}}
        
        self._initialized = True
    
    def _load_model(self) -> None:
        """YOLO 모델 로드 (OpenVINO 최적화 포함)"""
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics 패키지가 필요합니다. "
                "pip install ultralytics 로 설치하세요."
            )
        
        logger.info(f"🔽 YOLO 모델 로드 중: {self._model_path}")
        
        # 일반 PyTorch 모델 로드 (OpenVINO는 추후 도입)
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
        if not self._face_detector_loaded:
            self._load_face_detector()
            self._face_detector_loaded = True
    
    def _load_face_detector(self) -> None:
        """MediaPipe Face Detection 로드"""
        try:
            # MediaPipe import 테스트
            import mediapipe as mp
            
            # 최신 버전 (tasks API)
            if hasattr(mp, 'tasks'):
                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision
                
                # 모델 자동 다운로드 (Google에서 제공하는 기본 모델)
                import urllib.request
                import os
                
                model_path = 'blaze_face_short_range.tflite'
                if not os.path.exists(model_path):
                    logger.info("MediaPipe 모델 다운로드 중...")
                    urllib.request.urlretrieve(
                        'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite',
                        model_path
                    )
                
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.FaceDetectorOptions(
                    base_options=base_options,
                    min_detection_confidence=0.5
                )
                self._face_detector = vision.FaceDetector.create_from_options(options)
                self._face_detector_api = 'tasks'
                logger.info("✅ MediaPipe Face Detection 로드 완료 (tasks API)")
            # 구버전 (solutions API)
            elif hasattr(mp, 'solutions'):
                from mediapipe.python.solutions import face_detection as mp_face_detection
                
                self._face_detector = mp_face_detection.FaceDetection(
                    model_selection=0,  # 0: 2m 이내 근거리용, 1: 5m 원거리용
                    min_detection_confidence=0.5
                )
                self._face_detector_api = 'solutions'
                logger.info("✅ MediaPipe Face Detection 로드 완료 (solutions API)")
            else:
                logger.warning("⚠️ MediaPipe 버전 문제 (API 없음), 얼굴 필터링 비활성화")
                self._face_detector = None
                self._face_detector_api = None
        except ImportError as e:
            logger.warning(f"⚠️ MediaPipe 미설치: {e}, 얼굴 필터링 비활성화 (머리만 사용)")
            self._face_detector = None
            self._face_detector_api = None
        except Exception as e:
            logger.warning(f"⚠️ 얼굴 검출기 로드 실패: {e}, 머리만 사용")
            self._face_detector = None
            self._face_detector_api = None
    
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
        
        # YOLO 추론 + Tracking (BoT-SORT tracker)
        results = self._model.track(
            frame,
            conf=self._settings.YOLO_HEAD_CONFIDENCE,
            persist=True,  # 프레임 간 ID 유지
            tracker="botsort.yaml",  # BoT-SORT tracker 사용
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
                
                # Confidence 필터링
                if confidence < self._settings.YOLO_HEAD_CONFIDENCE:
                    continue
                
                # 바닥/화면 하단 오검출 필터링
                # Y 중심점이 화면 85% 이상 아래면 제외 (바닥 물체 가능성)
                cy_center = y + h / 2
                if cy_center > 0.85:
                    logger.debug(f"바닥 영역 검출 제외: y_center={cy_center:.2f}, conf={confidence:.2f}")
                    continue
                
                # 너무 작은 bbox 제외 (노이즈)
                if w < 0.05 or h < 0.05:
                    logger.debug(f"너무 작은 bbox 제외: w={w:.2f}, h={h:.2f}")
                    continue
                
                # Track ID 추출 (있는 경우)
                track_id = None
                if boxes.id is not None:
                    track_id = int(boxes.id[i].cpu().numpy())
                
                # Head bbox 생성 (추정 로직 없이 직접 사용)
                head_bbox = BoundingBox(x=x, y=y, width=w, height=h)
                
                # Bbox smoothing 적용
                head_bbox = self.smooth_bbox(head_bbox, track_id)
                
                detections.append(HeadDetection(
                    bbox=head_bbox,
                    confidence=confidence,
                    track_id=track_id
                ))
        
        # MediaPipe 보완 검출 (0명 또는 1명일 때)
        # - 0명: 전면/옆면만 있는 경우 YOLO가 놓칠 수 있음
        # - 1명: 한 명이 뒤통수, 다른 한 명이 전면일 경우
        if self._face_detector is not None and len(detections) <= 1:
            detections = self._supplement_with_face_detection(frame, detections)
        
        return detections
    
    def _supplement_with_face_detection(
        self, 
        frame: np.ndarray, 
        head_detections: List[HeadDetection]
    ) -> List[HeadDetection]:
        """
        MediaPipe 얼굴 검출로 YOLO가 놓친 머리 추가 검출 (보완용)
        
        YOLO는 뒤통수는 잘 잡지만 옆통수/전면을 놓치는 경우가 있음
        YOLO가 0-1명만 검출했을 때 MediaPipe로 추가 얼굴을 찾아서 보완
        
        Args:
            frame: 입력 프레임
            head_detections: YOLO로 검출된 머리 목록 (0-1개)
            
        Returns:
            YOLO + MediaPipe 보완 결과
        """
        frame_height, frame_width = frame.shape[:2]
        
        # 얼굴 검출 (API에 따라 다르게 처리)
        face_boxes = []
        
        if self._face_detector_api == 'tasks':
            # tasks API (최신 버전)
            import mediapipe as mp
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            face_results = self._face_detector.detect(mp_image)
            
            if not face_results.detections:
                logger.debug(f"MediaPipe 얼굴 미검출, YOLO만 사용 ({len(head_detections)}개)")
                return head_detections
            
            # tasks API bbox 추출
            for detection in face_results.detections:
                bbox = detection.bounding_box
                # tasks API: x, y, width, height (픽셀 단위)
                face_boxes.append({
                    'x': bbox.origin_x / frame_width,
                    'y': bbox.origin_y / frame_height,
                    'width': bbox.width / frame_width,
                    'height': bbox.height / frame_height
                })
        
        elif self._face_detector_api == 'solutions':
            # solutions API (구버전)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_results = self._face_detector.process(frame_rgb)
            
            if not face_results.detections:
                logger.debug(f"얼굴 미검출, 머리 검출만 사용 ({len(head_detections)}개)")
                return head_detections
            
            # solutions API bbox 추출
            for detection in face_results.detections:
                bbox = detection.location_data.relative_bounding_box
                # MediaPipe bbox: xmin, ymin, width, height (정규화)
                face_boxes.append({
                    'x': bbox.xmin,
                    'y': bbox.ymin,
                    'width': bbox.width,
                    'height': bbox.height
                })
        
        else:
            # API 정보 없음
            return head_detections
        
        if not face_boxes:
            logger.debug("MediaPipe 얼굴 미검출, YOLO 결과만 사용")
            return head_detections
        
        # YOLO 검출과 MediaPipe 얼굴들 매칭하여 추가 검출
        # YOLO가 0개 또는 1개일 수 있음
        matched_face_idx = None
        
        if len(head_detections) > 0:
            # YOLO 검출(1개)이 있으면 매칭 시도
            yolo_head = head_detections[0]
            yolo_cx, yolo_cy = yolo_head.bbox.center
            
            # YOLO와 겹치는 MediaPipe 얼굴 찾기
            for i, face in enumerate(face_boxes):
                face_cx = face['x'] + face['width'] / 2
                face_cy = face['y'] + face['height'] / 2
                
                # 거리 계산
                dist = np.sqrt((yolo_cx - face_cx)**2 + (yolo_cy - face_cy)**2)
                
                # IoU 계산
                yolo_x1 = yolo_head.bbox.x
                yolo_y1 = yolo_head.bbox.y
                yolo_x2 = yolo_x1 + yolo_head.bbox.width
                yolo_y2 = yolo_y1 + yolo_head.bbox.height
                
                face_x1 = face['x']
                face_y1 = face['y']
                face_x2 = face_x1 + face['width']
                face_y2 = face_y1 + face['height']
                
                inter_x1 = max(yolo_x1, face_x1)
                inter_y1 = max(yolo_y1, face_y1)
                inter_x2 = min(yolo_x2, face_x2)
                inter_y2 = min(yolo_y2, face_y2)
                
                has_overlap = False
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                    yolo_area = yolo_head.bbox.area
                    
                    # 교집합이 YOLO 면적의 20% 이상이거나 거리가 0.2 이내면 동일 인물
                    if inter_area / yolo_area > 0.2 or dist < 0.2:
                        has_overlap = True
                
                if has_overlap:
                    matched_face_idx = i
                    logger.debug(f"YOLO와 MediaPipe 얼굴 매칭됨: idx={i}, dist={dist:.3f}")
                    break
        
        # 매칭되지 않은 MediaPipe 얼굴들을 추가 검출로 추가
        result = list(head_detections)
        for i, face in enumerate(face_boxes):
            if i == matched_face_idx:
                continue  # 이미 YOLO로 검출된 사람
            
            # MediaPipe 얼굴을 HeadDetection으로 변환하여 추가
            face_bbox = BoundingBox(
                x=face['x'],
                y=face['y'],
                width=face['width'],
                height=face['height']
            )
            
            # confidence는 MediaPipe 기본값으로 설정 (YOLO보다 낮게)
            # 바닥/화면 하단 필터링 (MediaPipe도 동일하게 적용)
            face_cy_center = face['y'] + face['height'] / 2
            if face_cy_center > 0.85:
                logger.debug(f"MediaPipe 바닥 영역 검출 제외: y_center={face_cy_center:.2f}")
                continue
            
            # 너무 작은 bbox 제외
            if face['width'] < 0.05 or face['height'] < 0.05:
                logger.debug(f"MediaPipe 너무 작은 bbox 제외: w={face['width']:.2f}, h={face['height']:.2f}")
                continue
            
            face_detection = HeadDetection(
                bbox=face_bbox,
                confidence=0.6,  # MediaPipe 보완 검출 표시
                track_id=None  # MediaPipe는 tracking 없음
            )
            result.append(face_detection)
            
            face_cx = face['x'] + face['width'] / 2
            face_cy = face['y'] + face['height'] / 2
            logger.info(
                f"✅ MediaPipe로 추가 얼굴 검출: 중심({face_cx:.2f}, {face_cy:.2f}), "
                f"총 {len(result)}명"
            )
        
        return result
    
    def identify_parent_child(
        self,
        detections: List[HeadDetection],
        frame_shape: Tuple[int, int, int]
    ) -> Tuple[Tuple[float, float], Optional[HeadDetection], Optional[HeadDetection]]:
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
            (parent_center_pixel, child_detection, parent_detection)
            - parent_center_pixel: 부모 머리 중심 또는 프레임 중앙 (픽셀)
            - child_detection: 아이 HeadDetection 또는 None
            - parent_detection: 부모 HeadDetection 또는 None (1인칭 시 None)
        """
        height, width = frame_shape[:2]
        frame_center = (width / 2, height / 2)
        
        if len(detections) == 0:
            # 머리 미탐지
            logger.debug("머리 미탐지: 1인칭 모드 (아이 없음)")
            return frame_center, None, None
        
        if len(detections) == 1:
            # 1명만 탐지 → 1인칭 모드 (탐지된 머리 = 아이)
            child = detections[0]
            child.person_type = "child"
            logger.debug("1명 탐지: 1인칭 모드 (부모=중앙)")
            return frame_center, child, None
        
        # 2명 이상: 점수 기반 판별
        frame_center_x = 0.5
        frame_center_y = 0.5
        
        scores = []
        for det in detections:
            cx, cy = det.bbox.center
            
            # 아이 점수 계산 (높을수록 아이일 가능성)
            # 핵심: Y 위치가 가장 중요 (아래쪽 = 아이)
            y_score = cy  # Y 위치 (0~1, 아래쪽 = 높음)
            size_score = 1.0 - det.bbox.area  # 크기 (작을수록 = 높음)
            
            # Y 위치를 가장 중요하게 (아래 있는 사람 = 아이)
            child_score = (
                y_score * 10.0 +     # Y 위치 최우선 (아래쪽 = 아이)
                size_score * 1.0     # 크기는 보조 (작을수록 아이)
            )
            
            scores.append((det, child_score))
        
        # 가장 높은 점수 = 아이, 가장 낮은 점수 = 부모
        scores.sort(key=lambda x: x[1], reverse=True)
        child = scores[0][0]
        child.person_type = "child"
        
        parent_det = None
        if len(scores) > 1:
            parent_det = scores[-1][0]
            parent_det.person_type = "parent"
            parent_center = parent_det.center_pixel(width, height)
        else:
            parent_center = frame_center
        
        return parent_center, child, parent_det
    
    def smooth_bbox(self, bbox: BoundingBox, track_id: Optional[int]) -> BoundingBox:
        """
        Bounding box smoothing (EMA)
        
        Args:
            bbox: 현재 bbox
            track_id: tracking ID (None이면 smoothing 안 함)
            
        Returns:
            Smoothed bbox
        """
        if not self._settings.ENABLE_SMOOTHING or track_id is None:
            return bbox
        
        alpha = self._settings.SMOOTHING_ALPHA_BBOX
        
        # 이전 state 가져오기
        if track_id not in self._smoothing_state:
            self._smoothing_state[track_id] = {}
        
        state = self._smoothing_state[track_id]
        
        # 이전 bbox 없으면 현재 값 저장하고 반환
        if 'bbox' not in state:
            state['bbox'] = bbox
            return bbox
        
        prev = state['bbox']
        
        # EMA: new = alpha * curr + (1 - alpha) * prev
        smoothed = BoundingBox(
            x=alpha * bbox.x + (1 - alpha) * prev.x,
            y=alpha * bbox.y + (1 - alpha) * prev.y,
            width=alpha * bbox.width + (1 - alpha) * prev.width,
            height=alpha * bbox.height + (1 - alpha) * prev.height,
        )
        
        # 상태 업데이트
        state['bbox'] = smoothed
        
        return smoothed
    
    def smooth_pose(self, pitch: float, yaw: float, roll: float, track_id: Optional[int]) -> Tuple[float, float, float]:
        """
        Head pose smoothing (EMA)
        
        Args:
            pitch, yaw, roll: 현재 head pose (degrees)
            track_id: tracking ID (None이면 smoothing 안 함)
            
        Returns:
            Smoothed (pitch, yaw, roll)
        """
        if not self._settings.ENABLE_SMOOTHING or track_id is None:
            return pitch, yaw, roll
        
        alpha = self._settings.SMOOTHING_ALPHA_POSE
        
        # 이전 state 가져오기
        if track_id not in self._smoothing_state:
            self._smoothing_state[track_id] = {}
        
        state = self._smoothing_state[track_id]
        
        # 이전 pose 없으면 현재 값 저장하고 반환
        if 'pose' not in state:
            state['pose'] = (pitch, yaw, roll)
            return pitch, yaw, roll
        
        prev_pitch, prev_yaw, prev_roll = state['pose']
        
        # EMA with angle wrapping (yaw/roll: -180~180, pitch: -90~90)
        def smooth_angle(curr, prev, alpha):
            # 각도 차이가 180도 넘으면 wrapping 처리
            diff = curr - prev
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
            return prev + alpha * diff
        
        smoothed_pitch = alpha * pitch + (1 - alpha) * prev_pitch
        smoothed_yaw = smooth_angle(yaw, prev_yaw, alpha)
        smoothed_roll = smooth_angle(roll, prev_roll, alpha)
        
        # 상태 업데이트
        state['pose'] = (smoothed_pitch, smoothed_yaw, smoothed_roll)
        
        return smoothed_pitch, smoothed_yaw, smoothed_roll
    
    def smooth_gaze(self, gaze_x: float, gaze_y: float, gaze_z: float, track_id: Optional[int]) -> Tuple[float, float, float]:
        """
        Gaze direction smoothing (EMA)
        
        Args:
            gaze_x, gaze_y, gaze_z: 현재 gaze 방향 벡터
            track_id: tracking ID (None이면 smoothing 안 함)
            
        Returns:
            Smoothed (gaze_x, gaze_y, gaze_z) - 정규화됨
        """
        if not self._settings.ENABLE_SMOOTHING or track_id is None:
            return gaze_x, gaze_y, gaze_z
        
        alpha = self._settings.SMOOTHING_ALPHA_GAZE
        
        # 이전 state 가져오기
        if track_id not in self._smoothing_state:
            self._smoothing_state[track_id] = {}
        
        state = self._smoothing_state[track_id]
        
        # 이전 gaze 없으면 현재 값 저장하고 반환
        if 'gaze' not in state:
            state['gaze'] = (gaze_x, gaze_y, gaze_z)
            return gaze_x, gaze_y, gaze_z
        
        prev_x, prev_y, prev_z = state['gaze']
        
        # EMA
        smoothed_x = alpha * gaze_x + (1 - alpha) * prev_x
        smoothed_y = alpha * gaze_y + (1 - alpha) * prev_y
        smoothed_z = alpha * gaze_z + (1 - alpha) * prev_z
        
        # 벡터 정규화
        norm = np.sqrt(smoothed_x**2 + smoothed_y**2 + smoothed_z**2)
        if norm > 0:
            smoothed_x /= norm
            smoothed_y /= norm
            smoothed_z /= norm
        
        # 상태 업데이트
        state['gaze'] = (smoothed_x, smoothed_y, smoothed_z)
        
        return smoothed_x, smoothed_y, smoothed_z
    
    def clear_smoothing_state(self, track_id: Optional[int] = None) -> None:
        """
        Smoothing state 초기화
        
        Args:
            track_id: 특정 track_id만 초기화 (None이면 전체 초기화)
        """
        if track_id is None:
            self._smoothing_state.clear()
            logger.debug("모든 smoothing state 초기화")
        elif track_id in self._smoothing_state:
            del self._smoothing_state[track_id]
            logger.debug(f"track_id={track_id} smoothing state 초기화")
    
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
