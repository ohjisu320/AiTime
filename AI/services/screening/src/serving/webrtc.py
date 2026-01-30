import json
import logging
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from aiortc import (
    MediaStreamTrack,
    RTCDataChannel,
    RTCPeerConnection,
    RTCSessionDescription,
)
from fastapi import APIRouter, Request
from pydantic import BaseModel
from src.contracts.context import ROI, PreflightConfig, RunContext, make_repro_keys
from src.pipelines.orchestrator import PreflightOrchestrator

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
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    cfg = PreflightConfig(
        schema_version=raw.get("schema_version", "1.0"),
        task_type=raw.get("task_type", "PREFLIGHT_SCREENING"),
        window_sec=float(raw["window_sec"]),
        max_total_time_sec=float(raw["max_total_time_sec"]),
        sample_video_fps=int(raw["sample_video_fps"]),
        target_faces=int(raw["target_faces"]),
        audio_noise_dbfs_threshold=float(raw["audio"]["noise_dbfs_threshold"]),
        audio_noise_high_ratio_max=float(raw["audio"]["noise_high_ratio_max"]),
        video_luma_mean_threshold=float(raw["video"]["luma_mean_threshold"]),
        video_low_light_ratio_max=float(raw["video"]["low_light_ratio_max"]),
        faces_two_faces_ratio_min=float(raw["faces"]["two_faces_ratio_min"]),
        faces_min_face_area_ratio=float(raw["faces"]["min_face_area_ratio"]),
        roi_face_ratio_min=float(raw["roi"]["roi_face_ratio_min"]),
        roi_1=ROI(**raw["roi"]["roi_1"]),
        roi_2=ROI(**raw["roi"]["roi_2"]),
        debug_enabled=bool(raw["debug"]["enabled"]),
        debug_save_mismatch_only=bool(raw["debug"]["save_mismatch_only"]),
        debug_artifacts_dir=str(raw["debug"]["artifacts_dir"]),
    )
    return cfg


@router.post("/offer")
async def offer(req: OfferIn, request: Request) -> dict[str, Any]:
    cfg = load_config()

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
            channel.send(json.dumps(msg))

    orchestrator = PreflightOrchestrator(ctx, send=send)

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
