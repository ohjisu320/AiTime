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
      - luma_p10: float
      - low_light: bool
    """


class FrameQualityStage(Stage[FramePayload, FrameOut]):
    name = "frame_quality"

    def run(self, ctx: RunContext, payload: FramePayload) -> StageOutput[FrameOut]:
        t0 = time.perf_counter()
        flags = []

        frame: np.ndarray = payload["frame_bgr"]

        # downscale for speed
        H, W = frame.shape[:2]
        scale = 0.5 if max(H, W) >= 720 else 1.0
        if scale != 1.0:
            frame = cv2.resize(frame, (int(W * scale), int(H * scale)))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        luma_mean = float(np.mean(gray))
        luma_p10 = float(np.percentile(gray, 10))

        thr = ctx.config.video_luma_mean_threshold
        # 어두움 판단: mean이 낮으면 어둡다고 봄 (p10 조건 제거 - 검은 배경에 민감함)
        low_light = luma_mean < thr

        if low_light:
            flags.append(QualityFlag.LOW_LIGHT)

        out: FrameOut = {
            "luma_mean": luma_mean,
            "luma_p10": luma_p10,
            "low_light": bool(low_light),
        }
        metrics = self._metrics(
            t0, success=True, luma_mean=luma_mean, luma_p10=luma_p10, threshold=thr
        )
        return StageOutput(payload=out, stage_metrics=metrics, quality_flags=flags)
