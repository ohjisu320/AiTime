import cv2
import mediapipe as mp

from app.rtn.config import FaceDetConfig
from app.rtn.types import FrameBGR


class FaceDetectorMP:
    def __init__(self, cfg: FaceDetConfig) -> None:
        if not hasattr(mp, "solutions"):
            raise RuntimeError(
                "mediapipe에 solutions가 없습니다. "
                "(파이썬/mediapipe 호환성 문제 가능)\n"
                "권장: Python 3.10~3.12 + 안정 mediapipe",
            )

        self.cfg = cfg
        self.mp_fd = mp.solutions.face_detection
        self.detector = self.mp_fd.FaceDetection(
            model_selection=cfg.model_selection,
            min_detection_confidence=cfg.min_conf,
        )

    def detect(
        self, frame_bgr: FrameBGR
    ) -> list[tuple[float, float, float, float, float]]:
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.detector.process(rgb)

        out: list[tuple[float, float, float, float, float]] = []
        if not res.detections:
            return out

        for det in res.detections:
            score = float(det.score[0]) if det.score else 0.0
            b = det.location_data.relative_bounding_box
            x1 = b.xmin * w
            y1 = b.ymin * h
            x2 = (b.xmin + b.width) * w
            y2 = (b.ymin + b.height) * h
            out.append((x1, y1, x2, y2, score))
        return out
