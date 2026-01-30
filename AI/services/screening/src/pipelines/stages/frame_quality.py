import time

import cv2
import numpy as np
from src.contracts.context import QualityFlag, RunContext, StageOutput
from src.pipelines.stages.base import Stage


class FramePayload(dict):
    """
    payload keys:
      - frame_bgr: np.ndarray uint8 (H,W,3)
    """


class FrameOut(dict):
    """
    payload keys:
      - luma_mean: float
      - low_light: bool
    """


class FrameQualityStage(Stage[FramePayload, FrameOut]):
    name = "frame_quality"

    def run(self, ctx: RunContext, payload: FramePayload) -> StageOutput[FrameOut]:
        t0 = time.perf_counter()
        flags = []

        frame: np.ndarray = payload["frame_bgr"]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        luma_mean = float(np.mean(gray))

        thr = ctx.config.video_luma_mean_threshold
        low_light = luma_mean < thr
        if low_light:
            flags.append(QualityFlag.LOW_LIGHT)

        out: FrameOut = {"luma_mean": luma_mean, "low_light": bool(low_light)}
        metrics = self._metrics(t0, success=True, luma_mean=luma_mean, threshold=thr)
        return StageOutput(payload=out, stage_metrics=metrics, quality_flags=flags)
