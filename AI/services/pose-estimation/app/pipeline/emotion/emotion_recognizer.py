# app/pipeline/emotion/emotion_recognizer.py
"""
표정 인식 모듈.

EmotiEffLib (ONNX) 또는 hsemotion을 사용하여 얼굴 표정을 분류합니다.
"""

import logging
import numpy as np
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)

# 표정 인식기 상태
_recognizer_instance = None
_recognizer_available = None
_recognizer_backend = None


class EmotionLabel(str, Enum):
    """감정 레이블 (8가지)"""
    ANGER = "Anger"
    CONTEMPT = "Contempt"
    DISGUST = "Disgust"
    FEAR = "Fear"
    HAPPINESS = "Happiness"
    NEUTRAL = "Neutral"
    SADNESS = "Sadness"
    SURPRISE = "Surprise"


# EmotiEffLib 감정 순서 (모델 출력 순서)
EMOTION_LABELS = [
    EmotionLabel.ANGER,
    EmotionLabel.CONTEMPT,
    EmotionLabel.DISGUST,
    EmotionLabel.FEAR,
    EmotionLabel.HAPPINESS,
    EmotionLabel.NEUTRAL,
    EmotionLabel.SADNESS,
    EmotionLabel.SURPRISE,
]


def _load_recognizer(model_name: str = "enet_b0_8_best_vgaf"):
    """표정 인식기 지연 로딩"""
    global _recognizer_instance, _recognizer_available, _recognizer_backend
    
    if _recognizer_available is not None:
        return _recognizer_instance
    
    # 1. EmotiEffLib 시도 (ONNX)
    try:
        from emotiefflib import EmotiEffLibRecognizer
        _recognizer_instance = EmotiEffLibRecognizer(model_name=model_name)
        _recognizer_available = True
        _recognizer_backend = "EmotiEffLib"
        logger.info(f"✅ EmotiEffLib 로드 성공 (model: {model_name})")
        return _recognizer_instance
    except ImportError:
        logger.warning("⚠️ EmotiEffLib 없음, hsemotion으로 폴백 시도")
    except Exception as e:
        logger.warning(f"⚠️ EmotiEffLib 로드 실패: {e}, hsemotion으로 폴백 시도")
    
    # 2. hsemotion 시도
    try:
        from hsemotion.facial_emotions import HSEmotionRecognizer
        _recognizer_instance = HSEmotionRecognizer(model_name=model_name)
        _recognizer_available = True
        _recognizer_backend = "hsemotion"
        logger.info(f"✅ hsemotion 로드 성공 (model: {model_name})")
        return _recognizer_instance
    except ImportError:
        logger.warning("⚠️ hsemotion도 없음")
    except Exception as e:
        logger.warning(f"⚠️ hsemotion 로드 실패: {e}")
    
    # 3. 모두 실패
    _recognizer_available = False
    _recognizer_backend = None
    logger.error("❌ 표정 인식 모듈 로드 실패. 표정 분석이 비활성화됩니다.")
    return None


class EmotionRecognizer:
    """
    표정 인식기.
    
    EmotiEffLib (ONNX) 또는 hsemotion을 사용하여
    얼굴 이미지에서 8가지 감정을 분류합니다.
    """
    
    def __init__(self, model_name: str = "enet_b0_8_best_vgaf"):
        """
        EmotionRecognizer 초기화.
        
        Args:
            model_name: 사용할 모델 이름
        """
        self.model_name = model_name
        _load_recognizer(model_name)
        
        self.available = _recognizer_available
        self.backend = _recognizer_backend
        
        if self.available:
            logger.info(f"EmotionRecognizer 초기화 완료 (backend: {self.backend})")
        else:
            logger.warning("EmotionRecognizer 비활성화 상태")
    
    def predict(self, face_bgr: np.ndarray) -> Optional[dict[str, float]]:
        """
        얼굴 이미지에서 감정 분포 예측.
        
        Args:
            face_bgr: BGR 형식 얼굴 이미지
            
        Returns:
            감정별 확률 분포 또는 None (실패 시)
        """
        if not self.available or _recognizer_instance is None:
            return None
        
        try:
            if self.backend == "EmotiEffLib":
                return self._predict_emotieff(face_bgr)
            else:
                return self._predict_hsemotion(face_bgr)
        except Exception as e:
            logger.warning(f"표정 예측 실패: {e}")
            return None
    
    def _predict_emotieff(self, face_bgr: np.ndarray) -> dict[str, float]:
        """EmotiEffLib로 예측"""
        import cv2
        
        # RGB 변환
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        
        # 예측
        scores = _recognizer_instance.predict_emotions(face_rgb)
        
        # 딕셔너리로 변환
        result = {}
        for i, label in enumerate(EMOTION_LABELS):
            result[label.value] = float(scores[i]) if i < len(scores) else 0.0
        
        return result
    
    def _predict_hsemotion(self, face_bgr: np.ndarray) -> dict[str, float]:
        """hsemotion으로 예측"""
        import cv2
        
        # RGB 변환
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        
        # 예측 (hsemotion은 emotion, scores 튜플 반환)
        emotion, scores = _recognizer_instance.predict_emotions(face_rgb, logits=False)
        
        # 딕셔너리로 변환
        result = {}
        for i, label in enumerate(EMOTION_LABELS):
            result[label.value] = float(scores[i]) if i < len(scores) else 0.0
        
        return result
    
    def get_dominant_emotion(self, distribution: dict[str, float]) -> str:
        """
        가장 높은 확률의 감정 반환.
        
        Args:
            distribution: 감정별 확률 분포
            
        Returns:
            가장 높은 감정 레이블
        """
        return max(distribution, key=distribution.get)
    
    def is_joy(self, distribution: dict[str, float]) -> bool:
        """
        즐거움(Happiness)이 최대인지 확인.
        
        Args:
            distribution: 감정별 확률 분포
            
        Returns:
            Happiness가 가장 높은지 여부
        """
        return self.get_dominant_emotion(distribution) == EmotionLabel.HAPPINESS.value
