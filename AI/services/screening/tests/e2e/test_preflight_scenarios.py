import time
from dataclasses import dataclass

import numpy as np
from src.contracts.context import (
    ROI,
    FailureReason,
    PreflightConfig,
    RunContext,
    make_repro_keys,
)
from src.pipelines.orchestrator import PreflightOrchestrator


# ---- Fake stage to make e2e deterministic ----
@dataclass
class _FakeFaceOut:
    bboxes: list[tuple[int, int, int, int]]
    num_faces: int
    face_area_ratios: list[float]


class FakeFaceStage:
    name = "face_detect"

    def __init__(self, num_faces: int, bboxes: list[tuple[int, int, int, int]]) -> None:
        self._num_faces = num_faces
        self._bboxes = bboxes

    def run(self, ctx: RunContext, payload: dict) -> None:
        class _Out:
            def __init__(self, payload: dict) -> None:
                self.payload = payload
                self.stage_metrics = type(
                    "Metrics", (), {"latency_ms": 0.1, "success": True, "extra": {}}
                )()
                self.quality_flags = []

        area_ratios = [0.05] * len(self._bboxes)
        return _Out(
            {
                "bboxes": self._bboxes,
                "num_faces": self._num_faces,
                "face_area_ratios": area_ratios,
            }
        )


def _ctx() -> RunContext:
    cfg = PreflightConfig(
        schema_version="1.0",
        task_type="PREFLIGHT_SCREENING",
        window_sec=1.0,
        max_total_time_sec=4.0,  # 넉넉하게
        sample_video_fps=10,
        target_faces=2,
        audio_noise_dbfs_threshold=-35.0,
        audio_noise_high_ratio_max=0.2,
        video_luma_mean_threshold=60.0,
        video_low_light_ratio_max=0.2,
        faces_two_faces_ratio_min=0.8,
        faces_min_face_area_ratio=0.01,
        roi_face_ratio_min=0.8,
        roi_1=ROI(x0=0.0, y0=0.0, x1=0.5, y1=1.0),
        roi_2=ROI(x0=0.5, y0=0.0, x1=1.0, y1=1.0),
        min_video_samples=5,
        min_audio_samples=2,
        pass_hold_sec=0.5,
        debug_enabled=False,
        debug_save_mismatch_only=True,
        debug_artifacts_dir="artifacts/preflight",
    )
    repro = make_repro_keys(run_id="e2e_run")
    return RunContext(repro=repro, config=cfg, roi_1=cfg.roi_1, roi_2=cfg.roi_2)


def _run_case(
    video_luma: int,
    pcm_dbfs: float,
    num_faces: int,
    bboxes: list[tuple[int, int, int, int]],
) -> dict:
    ctx = _ctx()
    sent = []

    def send(msg: dict) -> None:
        sent.append(msg)

    orch = PreflightOrchestrator(ctx, send=send)

    # patch deterministic face stage
    orch.face_stage = FakeFaceStage(num_faces=num_faces, bboxes=bboxes)

    # synthetic frame: constant luma
    frame = np.full((240, 320, 3), video_luma, dtype=np.uint8)

    # synthetic audio chunk ~ 0.5 sec at 16k
    sr = 16000
    n = int(sr * 0.5)
    amp = 10 ** (pcm_dbfs / 20.0)
    pcm = (amp * np.random.randn(n)).astype(np.float32)

    # feed a few iterations
    t0 = time.monotonic()
    while (
        not orch.finished
        and (time.monotonic() - t0) < ctx.config.max_total_time_sec + 1.0
    ):
        orch.on_video_frame(frame)
        orch.on_audio_pcm(pcm, sr)
        time.sleep(0.1)

    # last result message
    results = [m for m in sent if m.get("type") == "result"]
    assert results, f"no result emitted, sent={sent[-5:]}"
    return results[-1]


def test_case_pass() -> None:
    bboxes = [(20, 50, 120, 180), (200, 50, 300, 180)]
    res = _run_case(video_luma=200, pcm_dbfs=-60.0, num_faces=2, bboxes=bboxes)
    assert res["passed"] is True


def test_case_fail_noise() -> None:
    bboxes = [(20, 50, 120, 180), (200, 50, 300, 180)]
    res = _run_case(video_luma=200, pcm_dbfs=-20.0, num_faces=2, bboxes=bboxes)
    assert res["passed"] is False
    assert res["failure_reason"] == FailureReason.FAIL_TIMEOUT
    assert res["details"]["representative_failure"] == FailureReason.FAIL_NOISE


def test_case_fail_low_light() -> None:
    bboxes = [(20, 50, 120, 180), (200, 50, 300, 180)]
    res = _run_case(video_luma=10, pcm_dbfs=-60.0, num_faces=2, bboxes=bboxes)
    assert res["passed"] is False
    assert res["failure_reason"] == FailureReason.FAIL_TIMEOUT
    assert res["details"]["representative_failure"] == FailureReason.FAIL_LOW_LIGHT


def test_case_fail_face_count() -> None:
    bboxes = [(20, 50, 120, 180)]
    res = _run_case(video_luma=200, pcm_dbfs=-60.0, num_faces=1, bboxes=bboxes)
    assert res["passed"] is False
    assert res["failure_reason"] == FailureReason.FAIL_TIMEOUT
    assert res["details"]["representative_failure"] == FailureReason.FAIL_FACE_COUNT


def test_case_fail_roi_mismatch() -> None:
    bboxes = [(20, 50, 120, 180), (30, 60, 110, 190)]
    res = _run_case(video_luma=200, pcm_dbfs=-60.0, num_faces=2, bboxes=bboxes)
    assert res["passed"] is False
    assert res["failure_reason"] == FailureReason.FAIL_TIMEOUT
    assert res["details"]["representative_failure"] == FailureReason.FAIL_ROI_MISMATCH
