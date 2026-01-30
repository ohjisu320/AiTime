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
        H0, W0 = frame.shape[:2]

        # resize for speed
        scale = 0.5 if max(H0, W0) >= 720 else 1.0
        if scale != 1.0:
            frame_s = cv2.resize(frame, (int(W0 * scale), int(H0 * scale)))
        else:
            frame_s = frame

        gray = cv2.cvtColor(frame_s, cv2.COLOR_BGR2GRAY)
        # minSize는 상황에 따라 조정 필요
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(max(30, int(40 * scale)), max(30, int(40 * scale))),
        )

        bboxes: list[BBox] = []
        area_ratios: list[float] = []
        frame_area = float(H0 * W0)

        inv = (1.0 / scale) if scale != 1.0 else 1.0

        for x, y, w, h in faces:
            x0 = int(x * inv)
            y0 = int(y * inv)
            x1 = int((x + w) * inv)
            y1 = int((y + h) * inv)
            bboxes.append((x0, y0, x1, y1))
            area_ratios.append(float(((x1 - x0) * (y1 - y0)) / frame_area))

        num_faces = len(bboxes)

        if num_faces < ctx.config.target_faces:
            flags.append(QualityFlag.TOO_FEW_FACES)
        elif num_faces > ctx.config.target_faces:
            flags.append(QualityFlag.TOO_MANY_FACES)

        min_ratio = ctx.config.faces_min_face_area_ratio
        if any(r < min_ratio for r in area_ratios):
            flags.append(QualityFlag.FACE_TOO_SMALL)

        out: FaceDetectOut = {
            "bboxes": bboxes,
            "num_faces": num_faces,
            "face_area_ratios": area_ratios,
        }
        metrics = self._metrics(t0, success=True, num_faces=num_faces, scale=scale)
        return StageOutput(payload=out, stage_metrics=metrics, quality_flags=flags)
