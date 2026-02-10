# app/pipeline/emotion/__init__.py
"""
아이 표정 분석 모듈.

비디오에서 아이 얼굴을 탐지하고 표정을 분류하여 감정 통계를 산출합니다.
"""

from .face_detector import FaceDetector, FaceDetection
from .child_selector import ChildFaceSelector
from .emotion_recognizer import EmotionRecognizer
from .expression_analyzer import ExpressionAnalyzer, ExpressionResult

__all__ = [
    "FaceDetector",
    "FaceDetection",
    "ChildFaceSelector",
    "EmotionRecognizer",
    "ExpressionAnalyzer",
    "ExpressionResult",
]
