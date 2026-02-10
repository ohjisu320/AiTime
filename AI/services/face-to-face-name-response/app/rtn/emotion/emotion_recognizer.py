import logging
import time

from app.rtn.config import EmotionConfig
from app.rtn.types import FrameBGR

logger = logging.getLogger(__name__)


class EmotionRecognizer:
    def __init__(self, cfg: EmotionConfig) -> None:
        self.cfg = cfg
        self.model = None
        self.enabled = cfg.enable
        self.labels = [
            "Anger",
            "Contempt",
            "Disgust",
            "Fear",
            "Happiness",
            "Neutral",
            "Sadness",
            "Surprise",
        ]

        if self.enabled:
            self._init_model()

    def _init_model(self) -> None:
        try:
            # Try importing EmotiEffLib (often installed as hsemotion or similar)
            # Default to hsemotion namespace if compatible
            try:
                from hsemotion.facial_emotions import HSEmotionRecognizer

                self.model = HSEmotionRecognizer(
                    model_name=self.cfg.model_name, device="cpu", is_mtcnn=False
                )
            except ImportError:
                # Fallback to EmotiEffLib (newer package name)
                from emotiefflib.facial_analysis import EmotiEffLibRecognizer

                self.model = EmotiEffLibRecognizer(
                    model_name=self.cfg.model_name, device="cpu"
                )

            logger.info(
                "EmotionRecognizer initialized with model=%s", self.cfg.model_name
            )

        except ImportError as e:
            logger.warning(
                "EmotiEffLib/hsemotion not found: %s. Emotion recognition disabled.", e
            )
            self.enabled = False
        except Exception as e:
            logger.warning("Failed to load Emotion model: %s. Feature disabled.", e)
            self.enabled = False

    def predict(self, face_bgr: FrameBGR) -> dict[str, float] | None:
        if not self.enabled or self.model is None:
            return None

        t0 = time.perf_counter()
        try:
            # EmotiEffLib/HSEmotion usually expects RGB
            # But opencv is BGR. check if library handles it or we need conversion.
            # Most deep learning libs expect RGB. Let's convert.
            import cv2
            import numpy as np

            face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)

            # predict returns [scores], [emotion_idx] usually,
            # or just emotion_idx, scores
            # The signature varies.
            # standard hsemotion: detect_emotions(image) -> top_emotion, scores
            emotion, scores = self.model.predict_emotions(face_rgb, logits=False)

            # DEBUG: 반환값 형식 확인
            logger.debug(
                "predict_emotions returned: \
                    emotion=%s (type=%s), scores type=%s shape=%s",
                emotion,
                type(emotion).__name__,
                type(scores).__name__,
                getattr(scores, "shape", "N/A"),
            )

            # scores가 numpy 배열인 경우 처리
            if isinstance(scores, np.ndarray):
                # 2D 배열인 경우 (batch=1) 첫 번째 행 사용
                if scores.ndim == 2:
                    scores = scores[0]
                scores = scores.tolist()

            # scores is usually a list of floats.
            dist = {
                label: float(score)
                for label, score in zip(self.labels, scores, strict=False)
            }

            # Monitoring Latency LOG (DEBUG level)
            latency = (time.perf_counter() - t0) * 1000
            if latency > self.cfg.p95_latency_ms_max:
                logger.warning("Emotion inference slow: %.1fms", latency)
            else:
                logger.debug(
                    "Emotion inference: %.1fms latency, dist=%s", latency, dist
                )

            return dist

        except Exception as e:
            logger.debug("Emotion prediction failed: %s", e, exc_info=True)
            return None
