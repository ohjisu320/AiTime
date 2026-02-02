import json
import logging
import uuid
from datetime import datetime
from typing import Any

import numpy as np
from aiortc import (
    MediaStreamTrack,
    RTCDataChannel,
    RTCPeerConnection,
    RTCSessionDescription,
)
from fastapi import APIRouter, Request
from pydantic import BaseModel
from src.contracts.context import ROI, RunContext, make_repro_keys
from src.monitoring.artifacts import DebugArtifactSaver
from src.monitoring.run_logger import JsonlRunLogger
from src.pipelines.orchestrator import PreflightOrchestrator
from src.serving.preflight_config import PreflightConfig, load_preflight_config

router = APIRouter()
logger = logging.getLogger(__name__)

PCS: set[RTCPeerConnection] = set()


class OfferIn(BaseModel):
    sdp: str
    type: str
    # optional client overrides
    roi_1: ROI | None = None
    roi_2: ROI | None = None
    client_info: dict[str, Any] = {}


def load_config(path: str = "configs/preflight.yaml") -> PreflightConfig:
    # Backwards-compatible name for existing imports/tests.
    return load_preflight_config(path)


@router.post("/offer")
async def offer(req: OfferIn, request: Request) -> dict[str, Any]:
    cfg = load_preflight_config()

    run_id = f"preflight_{uuid.uuid4().hex[:10]}"
    repro = make_repro_keys(
        run_id=run_id,
        code_sha=request.headers.get("x-code-sha", "unknown"),
        config_version=request.headers.get("x-config-version", "unknown"),
        env_lock_hash=request.headers.get("x-env-lock-hash", "unknown"),
    )

    roi_1 = req.roi_1 or cfg.roi_1
    roi_2 = req.roi_2 or cfg.roi_2

    ctx = RunContext(
        repro=repro,
        trace_id=request.headers.get("x-trace-id", run_id),
        config=cfg,
        roi_1=roi_1,
        roi_2=roi_2,
        client_info=req.client_info or {},
    )

    pc = RTCPeerConnection()
    PCS.add(pc)

    channel = None

    def send(msg: dict) -> None:
        if channel and channel.readyState == "open":
            channel.send(json.dumps(msg, ensure_ascii=False))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_id = f"{ts}_{run_id}"

    run_logger = JsonlRunLogger(
        run_id=timestamp_id,
        trace_id=ctx.trace_id,
        logs_dir=ctx.config.logs_dir,
        enabled=ctx.config.logs_enabled,
    )

    artifact_saver = DebugArtifactSaver(
        run_id=timestamp_id,
        base_dir=ctx.config.debug_artifacts_dir,
        enabled=ctx.config.debug_enabled,
        save_fail_only=ctx.config.debug_save_mismatch_only,
        sample_rate=ctx.config.debug_sample_rate,
        save_on_flags=ctx.config.debug_save_on_flags,
        roi_1=ctx.roi_1,
        roi_2=ctx.roi_2,
    )

    orchestrator = PreflightOrchestrator(
        ctx, send=send, run_logger=run_logger, artifact_saver=artifact_saver
    )

    @pc.on("datachannel")
    def on_datachannel(ch: RTCDataChannel) -> None:
        nonlocal channel
        channel = ch

        @ch.on("message")
        def on_message(message: str | bytes) -> None:
            # Optionally allow ROI update mid-session
            try:
                obj = json.loads(message) if isinstance(message, str) else {}
                if obj.get("type") == "set_roi":
                    if "roi_1" in obj:
                        ctx.roi_1 = ROI(**obj["roi_1"])
                    if "roi_2" in obj:
                        ctx.roi_2 = ROI(**obj["roi_2"])
            except Exception:
                pass

    @pc.on("track")
    async def on_track(track: MediaStreamTrack) -> None:
        if track.kind == "video":
            count = 0
            while not orchestrator.finished:
                frame = await track.recv()
                count += 1
                if count % 30 == 0:
                    logger.info(f"[{run_id}] video frames received: {count}")
                img = frame.to_ndarray(format="bgr24")
                orchestrator.on_video_frame(img)

        elif track.kind == "audio":
            while not orchestrator.finished:
                frame = await track.recv()
                # aiortc AudioFrame -> numpy float32 (-1..1) (mono mix)
                pcm = frame.to_ndarray()
                # pcm shape could be (channels, samples) or (samples,)
                if pcm.ndim == 2:
                    pcm = pcm.mean(axis=0)
                pcm = pcm.astype(np.float32)
                # if int16-like, normalize (best-effort)
                if pcm.max() > 1.5 or pcm.min() < -1.5:
                    pcm = pcm / 32768.0
                orchestrator.on_audio_pcm(pcm, sample_rate=int(frame.sample_rate))

    offer = RTCSessionDescription(sdp=req.sdp, type=req.type)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
        "run_id": run_id,
    }
