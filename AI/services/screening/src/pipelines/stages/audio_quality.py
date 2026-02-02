import math
import time

import numpy as np
from src.contracts.context import QualityFlag, RunContext, StageOutput
from src.pipelines.stages.base import Stage


class AudioPayload(dict):
    """
    payload keys:
      - pcm: np.ndarray float32 [-1..1], shape (n,)
      - sample_rate: int
    """


class AudioOut(dict):
    """
    payload keys:
      - rms_dbfs: float
      - noisy: bool
    """


class AudioQualityStage(Stage[AudioPayload, AudioOut]):
    name = "audio_quality"

    def run(self, ctx: RunContext, payload: AudioPayload) -> StageOutput[AudioOut]:
        t0 = time.perf_counter()
        flags = []

        pcm: np.ndarray = payload["pcm"]
        # avoid nan
        if pcm.size == 0:
            rms_dbfs = -120.0
        else:
            rms = float(np.sqrt(np.mean(np.square(pcm.astype(np.float32))) + 1e-12))
            rms_dbfs = 20.0 * math.log10(max(rms, 1e-12))

        thr = ctx.config.audio_noise_dbfs_threshold
        noisy = rms_dbfs > thr
        if noisy:
            flags.append(QualityFlag.NOISE_HIGH)

        out: AudioOut = {"rms_dbfs": float(rms_dbfs), "noisy": bool(noisy)}
        metrics = self._metrics(t0, success=True, rms_dbfs=rms_dbfs, threshold=thr)
        return StageOutput(payload=out, stage_metrics=metrics, quality_flags=flags)
