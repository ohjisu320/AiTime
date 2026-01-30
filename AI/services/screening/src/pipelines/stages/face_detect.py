import time

import cv2
import numpy as np
from src.contracts.context import QualityFlag, RunContext, StageOutput
from src.pipelines.stages.base import Stage

BBox = tuple[int, int, int, int]  # x0,y0,x1,y1


class FaceDetectPayload(dict):
    """
    payload keys:
      - frame_bgr: np.ndarray uint8 (H,W,3)
    """


class FaceDetectOut(dict):
    """
    payload keys:
      - bboxes: list[BBox]
      - num_faces: int
      - face_area_ratios: list[float]  # bbox area / frame area
    """


class FaceDetectStage(Stage[FaceDetectPayload, FaceDetectOut]):
    """
    Skeleton detector:
      - default: OpenCV Haar cascade (quick baseline)
      - TODO: swap to MediaPipe / your existing face detector for production
    """

    name = "face_detect"

    def __init__(self) -> None:
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def run(
        self, ctx: RunContext, payload: FaceDetectPayload
    ) -> StageOutput[FaceDetectOut]:
        t0 = time.perf_counter()
        flags: list[QualityFlag] = []

        frame: np.ndarray = payload["frame_bgr"]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )

        bboxes: list[BBox] = []
        area_ratios: list[float] = []
        H, W = frame.shape[:2]
        frame_area = float(H * W)

        for x, y, w, h in faces:
            x0, y0 = int(x), int(y)
            x1, y1 = int(x + w), int(y + h)
            bboxes.append((x0, y0, x1, y1))
            area_ratios.append(float((w * h) / frame_area))

        num_faces = len(bboxes)

        # Face count flags
        if num_faces < ctx.config.target_faces:
            flags.append(QualityFlag.TOO_FEW_FACES)
        elif num_faces > ctx.config.target_faces:
            flags.append(QualityFlag.TOO_MANY_FACES)

        # Too-small face flags (optional)
        min_ratio = ctx.config.faces_min_face_area_ratio
        if any(r < min_ratio for r in area_ratios):
            flags.append(QualityFlag.FACE_TOO_SMALL)

        out: FaceDetectOut = {
            "bboxes": bboxes,
            "num_faces": num_faces,
            "face_area_ratios": area_ratios,
        }
        metrics = self._metrics(t0, success=True, num_faces=num_faces)
        return StageOutput(payload=out, stage_metrics=metrics, quality_flags=flags)
