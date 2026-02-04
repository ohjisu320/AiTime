# app/pipeline/emotion/expression_analyzer.py
"""
표정 분석 통합 모듈.

얼굴 탐지, 아이 선택, 표정 분류를 통합하여
전체 영상에 대한 감정 통계를 산출합니다.
"""

import logging
import time
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

from .face_detector import FaceDetector, FaceDetection
from .child_selector import ChildFaceSelector
from .emotion_recognizer import EmotionRecognizer, EMOTION_LABELS

logger = logging.getLogger(__name__)


@dataclass
class FrameExpressionResult:
    """프레임별 표정 분석 결과"""
    frame_index: int
    face_detected: bool
    child_face_selected: bool
    dominant_emotion: Optional[str] = None
    emotion_distribution: Optional[dict[str, float]] = None


@dataclass
class ExpressionResult:
    """
    표정 분석 최종 결과.
    
    Attributes:
        total_frames_analyzed: 분석된 총 프레임 수
        valid_detections: 유효한 얼굴 탐지 수
        expression_counts: 감정별 프레임 수
        expression_ratios: 감정별 비율
        joy_count: 즐거움(Happiness) 프레임 수
        joy_ratio: 즐거움 비율
        joy_detected: 즐거움 탐지 여부
        dominant_emotion: 가장 많이 나타난 감정
        processing_time_sec: 처리 시간
    """
    total_frames_analyzed: int
    valid_detections: int
    expression_counts: dict[str, int]
    expression_ratios: dict[str, float]
    joy_count: int
    joy_ratio: float
    joy_detected: bool
    dominant_emotion: str
    processing_time_sec: float
    frame_results: list[FrameExpressionResult] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (API 응답용)"""
        return {
            "total_frames_analyzed": self.total_frames_analyzed,
            "valid_detections": self.valid_detections,
            "expression_counts": self.expression_counts,
            "expression_ratios": {k: round(v, 4) for k, v in self.expression_ratios.items()},
            "joy_count": self.joy_count,
            "joy_ratio": round(self.joy_ratio, 4),
            "joy_detected": self.joy_detected,
            "dominant_emotion": self.dominant_emotion,
            "processing_time_sec": round(self.processing_time_sec, 2),
        }
    
    def to_summary_dict(self) -> dict[str, Any]:
        """간결한 요약 딕셔너리 (RabbitMQ 응답용)"""
        return {
            "detected": self.joy_detected,
            "count": self.joy_count,
            "ratio": round(self.joy_ratio, 4),
            "dominant": self.dominant_emotion,
            "distribution": {k: round(v, 4) for k, v in self.expression_ratios.items()},
        }


@dataclass
class EmotionConfig:
    """표정 분석 설정"""
    enable: bool = True
    skip_frames: int = 5
    min_face_size: int = 64
    model_name: str = "enet_b0_8_best_vgaf"
    joy_threshold: float = 0.1  # 즐거움 탐지 임계값 (비율)
    face_confidence_threshold: float = 0.9


class ExpressionAnalyzer:
    """
    표정 분석 통합 클래스.
    
    비디오 프레임에서 아이 얼굴을 탐지하고 표정을 분류하여
    전체 영상에 대한 감정 통계를 산출합니다.
    """
    
    def __init__(self, config: Optional[EmotionConfig] = None):
        """
        ExpressionAnalyzer 초기화.
        
        Args:
            config: 표정 분석 설정
        """
        self.config = config or EmotionConfig()
        
        if not self.config.enable:
            logger.info("ExpressionAnalyzer 비활성화 상태")
            self.available = False
            return
        
        # 모듈 초기화
        self.face_detector = FaceDetector(
            min_face_size=self.config.min_face_size,
            confidence_threshold=self.config.face_confidence_threshold
        )
        self.child_selector = ChildFaceSelector()
        self.emotion_recognizer = EmotionRecognizer(model_name=self.config.model_name)
        
        self.available = self.emotion_recognizer.available
        
        if self.available:
            logger.info(
                f"ExpressionAnalyzer 초기화 완료: "
                f"skip_frames={self.config.skip_frames}, "
                f"model={self.config.model_name}"
            )
        else:
            logger.warning("ExpressionAnalyzer: 표정 인식 모듈 없음, 비활성화")
    
    def analyze(
        self,
        frames: list[np.ndarray],
        child_head_positions: Optional[list[Optional[tuple[float, float]]]] = None,
        parent_head_positions: Optional[list[Optional[tuple[float, float]]]] = None
    ) -> ExpressionResult:
        """
        프레임 목록에서 표정 분석 수행.
        
        Args:
            frames: BGR 프레임 목록
            child_head_positions: 각 프레임의 아이 머리 위치 (Pose에서 추출)
            parent_head_positions: 각 프레임의 부모 머리 위치 (제외용)
            
        Returns:
            ExpressionResult 객체
        """
        start_time = time.time()
        
        # 비활성화 상태면 빈 결과 반환
        if not self.available:
            return self._empty_result(len(frames), time.time() - start_time)
        
        # 감정 카운트 초기화
        expression_counts = {label.value: 0 for label in EMOTION_LABELS}
        frame_results = []
        valid_detections = 0
        total_analyzed = 0
        
        # skip_frames 간격으로 샘플링
        for i in range(0, len(frames), self.config.skip_frames):
            if i >= len(frames):
                break
            
            total_analyzed += 1
            frame = frames[i]
            
            # 아이/부모 머리 위치
            child_head = child_head_positions[i] if child_head_positions and i < len(child_head_positions) else None
            parent_head = parent_head_positions[i] if parent_head_positions and i < len(parent_head_positions) else None
            
            # 분석 수행
            result = self._analyze_single_frame(
                frame, i, child_head, parent_head
            )
            frame_results.append(result)
            
            # 카운트 업데이트
            if result.face_detected and result.child_face_selected and result.dominant_emotion:
                valid_detections += 1
                expression_counts[result.dominant_emotion] += 1
        
        # 통계 계산
        expression_ratios = {}
        for label, count in expression_counts.items():
            expression_ratios[label] = count / valid_detections if valid_detections > 0 else 0.0
        
        # 즐거움 통계
        joy_count = expression_counts.get("Happiness", 0)
        joy_ratio = joy_count / valid_detections if valid_detections > 0 else 0.0
        joy_detected = joy_ratio >= self.config.joy_threshold
        
        # 가장 많이 나타난 감정
        dominant_emotion = max(expression_counts, key=expression_counts.get) if valid_detections > 0 else "Neutral"
        
        processing_time = time.time() - start_time
        
        result = ExpressionResult(
            total_frames_analyzed=total_analyzed,
            valid_detections=valid_detections,
            expression_counts=expression_counts,
            expression_ratios=expression_ratios,
            joy_count=joy_count,
            joy_ratio=joy_ratio,
            joy_detected=joy_detected,
            dominant_emotion=dominant_emotion,
            processing_time_sec=processing_time,
            frame_results=frame_results
        )
        
        logger.info(
            f"표정 분석 완료: frames={total_analyzed}, "
            f"valid={valid_detections}, "
            f"joy={joy_count} ({joy_ratio:.1%}), "
            f"dominant={dominant_emotion}, "
            f"time={processing_time:.2f}s"
        )
        
        return result
    
    def _analyze_single_frame(
        self,
        frame: np.ndarray,
        frame_index: int,
        child_head_pos: Optional[tuple[float, float]],
        parent_head_pos: Optional[tuple[float, float]]
    ) -> FrameExpressionResult:
        """단일 프레임 표정 분석"""
        # 1. 얼굴 탐지
        faces = self.face_detector.detect(frame)
        if not faces:
            return FrameExpressionResult(
                frame_index=frame_index,
                face_detected=False,
                child_face_selected=False
            )
        
        # 2. 아이 얼굴 선택
        child_face = self.child_selector.select(
            faces, child_head_pos, parent_head_pos
        )
        if child_face is None:
            return FrameExpressionResult(
                frame_index=frame_index,
                face_detected=True,
                child_face_selected=False
            )
        
        # 3. 얼굴 크롭
        face_crop = self.face_detector.crop_face(frame, child_face)
        
        # 4. 표정 분류
        distribution = self.emotion_recognizer.predict(face_crop)
        if distribution is None:
            return FrameExpressionResult(
                frame_index=frame_index,
                face_detected=True,
                child_face_selected=True
            )
        
        dominant = self.emotion_recognizer.get_dominant_emotion(distribution)
        
        return FrameExpressionResult(
            frame_index=frame_index,
            face_detected=True,
            child_face_selected=True,
            dominant_emotion=dominant,
            emotion_distribution=distribution
        )
    
    def _empty_result(self, total_frames: int, processing_time: float) -> ExpressionResult:
        """비활성화 시 빈 결과 반환"""
        empty_counts = {label.value: 0 for label in EMOTION_LABELS}
        empty_ratios = {label.value: 0.0 for label in EMOTION_LABELS}
        
        return ExpressionResult(
            total_frames_analyzed=0,
            valid_detections=0,
            expression_counts=empty_counts,
            expression_ratios=empty_ratios,
            joy_count=0,
            joy_ratio=0.0,
            joy_detected=False,
            dominant_emotion="Neutral",
            processing_time_sec=processing_time,
            frame_results=[]
        )
    
    def analyze_from_video_frames(
        self,
        frame_generator,
        frame_persons: list,
        skip_frames: Optional[int] = None
    ) -> ExpressionResult:
        """
        비디오 프레임 Generator와 Pose 결과로부터 분석.
        
        기존 MotionAnalyzer의 프레임과 frame_persons 결과를 활용합니다.
        
        Args:
            frame_generator: 프레임 Generator
            frame_persons: 각 프레임의 FramePersons 객체 리스트
            skip_frames: 프레임 건너뛰기 간격 (None이면 config 사용)
            
        Returns:
            ExpressionResult 객체
        """
        skip = skip_frames or self.config.skip_frames
        
        # Generator를 리스트로 변환 (이미 추출된 경우)
        if not isinstance(frame_generator, list):
            frames = list(frame_generator)
        else:
            frames = frame_generator
        
        # Pose에서 머리 위치 추출
        child_heads = []
        parent_heads = []
        
        for fp in frame_persons:
            # 아이 머리 위치
            if fp.child is not None and hasattr(fp.child, 'keypoints'):
                child_head = self.child_selector.get_head_position_from_pose(
                    fp.child.keypoints,
                    frames[0].shape[:2] if frames else (720, 1280)
                )
                child_heads.append(child_head)
            else:
                child_heads.append(None)
            
            # 부모 머리 위치
            if fp.parent is not None and hasattr(fp.parent, 'keypoints'):
                parent_head = self.child_selector.get_head_position_from_pose(
                    fp.parent.keypoints,
                    frames[0].shape[:2] if frames else (720, 1280)
                )
                parent_heads.append(parent_head)
            else:
                parent_heads.append(None)
        
        return self.analyze(frames, child_heads, parent_heads)
