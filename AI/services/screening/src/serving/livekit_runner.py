import asyncio
import contextlib
import json
import logging
import time
from datetime import datetime

import cv2
import httpx
import numpy as np
from livekit import rtc
from src.contracts.context import ROI, RunContext, make_repro_keys
from src.monitoring.artifacts import DebugArtifactSaver
from src.monitoring.run_logger import JsonlRunLogger
from src.pipelines.orchestrator import PreflightOrchestrator
from src.serving.preflight_config import load_preflight_config
from src.serving.settings import ANALYSIS_HARD_TIMEOUT_SEC, BACKEND_URL, LIVEKIT_URL

logger = logging.getLogger(__name__)


class LiveKitRunError(RuntimeError):
    pass


async def notify_backend(room_name: str, status: str) -> None:
    """Notify Spring Backend that screening is finished."""
    url = f"{BACKEND_URL.rstrip('/')}/api/v1/screening/complete"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url, json={"roomName": room_name, "status": status}, timeout=10.0
            )
    except Exception as e:
        # Do not raise:
        # the screening can be considered completed even if backend callback fails.
        logger.exception("notify_backend failed: %s", e)


def _to_bgr(frame_or_event: any) -> np.ndarray:
    """Convert LiveKit video frame to OpenCV BGR."""
    # LiveKit Python SDK may return VideoFrameEvent wrapper; extract .frame if needed
    frame = getattr(frame_or_event, "frame", frame_or_event)

    # Try multiple methods to extract numpy array from VideoFrame
    # Method 1: to_ndarray (older SDK versions)
    if hasattr(frame, "to_ndarray"):
        img_rgb = frame.to_ndarray(format="rgb24")
        return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    # Method 2: data + width + height (newer SDK versions)
    # VideoFrame.data is memoryview, type indicates pixel format
    width = frame.width
    height = frame.height
    data = frame.data
    buffer_type = getattr(frame, "type", None)

    # Convert memoryview to numpy
    arr = np.frombuffer(data, dtype=np.uint8)
    expected_size = arr.size

    # Determine format based on size and type
    # I420/YUV420: size = width * height * 1.5
    i420_size = int(width * height * 1.5)
    rgba_size = width * height * 4
    rgb_size = width * height * 3

    type_name = str(buffer_type).upper() if buffer_type is not None else ""

    # Check for I420/YUV formats first (most common in WebRTC)
    if "I420" in type_name or "YUV" in type_name or expected_size == i420_size:
        # I420 format: Y plane (w*h) + U plane (w/2 * h/2) + V plane (w/2 * h/2)
        yuv = arr.reshape((int(height * 1.5), width))
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)

    if "ARGB" in type_name:
        arr = arr.reshape((height, width, 4))
        # ARGB -> BGR: skip first channel (A), reverse RGB
        return arr[:, :, 1:4][:, :, ::-1].copy()
    elif "BGRA" in type_name:
        arr = arr.reshape((height, width, 4))
        return arr[:, :, :3].copy()  # Just take BGR
    elif "RGBA" in type_name or expected_size == rgba_size:
        arr = arr.reshape((height, width, 4))
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    elif "RGB" in type_name or expected_size == rgb_size:
        arr = arr.reshape((height, width, 3))
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    # Fallback: try I420 (most common WebRTC format)
    try:
        yuv = arr.reshape((int(height * 1.5), width))
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
    except Exception:
        pass

    # Last resort: try RGBA then RGB
    try:
        arr = arr.reshape((height, width, 4))
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    except Exception:
        arr = arr.reshape((height, width, 3))
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def _pcm_to_mono_float32(pcm: np.ndarray) -> np.ndarray:
    if pcm.ndim == 2:
        pcm = pcm.mean(axis=0)
    pcm = pcm.astype(np.float32)
    # best-effort normalization (if int16-like range)
    if pcm.size and (pcm.max() > 1.5 or pcm.min() < -1.5):
        pcm = pcm / 32768.0
    return pcm


def _translate_message(msg: dict) -> dict:
    """Map internal preflight messages -> project DataChannel schema.

    API 명세 필드와 하위 호환 필드(_compat)를 모두 포함합니다.
    """
    t = msg.get("type")
    # internal contract: hint/progress/result
    if t == "hint":
        return {
            # API 명세 필드
            "type": "guide",
            "message": msg.get("hint", ""),
            "person_count": msg.get("person_count", 0),
            "distance": msg.get("distance", 0),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            # 하위 호환 필드 (명세에 없음)
            "_compat": {
                "flags": msg.get("flags", []),
            },
        }
    if t == "progress":
        # progress 메시지는 명세에 없음 - AI 확장 필드로 유지
        return {
            "type": "progress",
            "progress": msg.get("progress", 0.0),
            "ratios": msg.get("ratios", {}),
            "scores": msg.get("scores", {}),
            "flags": msg.get("flags", []),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    if t == "result":
        passed = bool(msg.get("passed"))
        return {
            # API 명세 필드
            "type": "screening_complete",
            "status": "success" if passed else "failure",
            "summary": {
                "total_frames": msg.get("total_frames", 0),
                "valid_frames": msg.get("valid_frames", 0),
                "confidence": msg.get("confidence", 0.0),
            },
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            # 하위 호환 필드 (명세에 없음)
            "_compat": {
                "passed": passed,
                "failure_reason": msg.get("failure_reason"),
                "flags": msg.get("flags", []),
                "ratios": msg.get("ratios", {}),
                "scores": msg.get("scores", {}),
                "details": msg.get("details", {}),
            },
        }
    return msg


async def _publish_error(room: rtc.Room, message: str, code: str) -> None:
    """Publish error message to DataChannel."""
    error_msg = {
        "type": "error",
        "message": message,
        "code": code,
    }
    data = json.dumps(error_msg).encode()
    await room.local_participant.publish_data(data, reliable=True)


async def run_preflight_livekit(
    *,
    room_name: str,
    token: str,
    session_id: int,
    participant_name: str,
    roi_1: ROI | None = None,
    roi_2: ROI | None = None,
    client_info: dict | None = None,
    repro_overrides: dict | None = None,
) -> None:
    """
    Join LiveKit room,
    consume A/V tracks,
    run preflight pipeline,
    publish datachannel hints/results.
    """
    cfg = load_preflight_config()

    # --- Run IDs / repro keys ---
    suffix = hex(int(time.time()))[2:]
    run_id = f"preflight_{session_id}_{suffix}"
    repro = make_repro_keys(
        run_id=run_id,
        code_sha=(repro_overrides or {}).get("code_sha", "unknown"),
        config_version=(repro_overrides or {}).get("config_version", "unknown"),
        env_lock_hash=(repro_overrides or {}).get("env_lock_hash", "unknown"),
    )

    ctx = RunContext(
        repro=repro,
        trace_id=(repro_overrides or {}).get("trace_id", run_id),
        config=cfg,
        roi_1=roi_1 or cfg.roi_1,
        roi_2=roi_2 or cfg.roi_2,
        client_info=client_info or {},
    )

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

    room = rtc.Room()
    done = asyncio.Event()
    result_status: str | None = None

    async def publish(msg: dict) -> None:
        nonlocal result_status
        try:
            out = _translate_message(msg)
            logger.info("[publish] sending type=%s", msg.get("type"))
            payload = json.dumps(out, ensure_ascii=False).encode("utf-8")
            # IMPORTANT: publish_data uses positional arg only in some versions
            await room.local_participant.publish_data(payload)
            logger.info("[publish] sent successfully type=%s", msg.get("type"))

            if msg.get("type") == "result":
                result_status = "success" if bool(msg.get("passed")) else "failure"
                done.set()
        except Exception as e:
            logger.exception("[publish] FAILED type=%s error=%s", msg.get("type"), e)

    def send(msg: dict) -> None:
        # orchestrator calls this synchronously.
        asyncio.create_task(publish(msg))

    orchestrator = PreflightOrchestrator(
        ctx, send=send, run_logger=run_logger, artifact_saver=artifact_saver
    )

    tasks: set[asyncio.Task] = set()

    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant) -> None:
        logger.info("[preflight] participant_connected: %s", participant.identity)

    @room.on("track_published")
    def on_track_published(
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        logger.info(
            "[preflight] track_published: participant=%s kind=%s",
            participant.identity,
            publication.kind,
        )

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        logger.info(
            "[preflight] track_subscribed: participant=%s kind=%s",
            participant.identity,
            track.kind,
        )
        # Consume tracks only from the target participant if you want strict filtering.
        # Here, we accept first available A/V tracks.
        if track.kind == rtc.TrackKind.KIND_VIDEO:

            async def _consume_video() -> None:
                try:
                    logger.info("[preflight] starting video consumption")
                    vs = rtc.VideoStream(track)
                    frame_count = 0
                    async for frame in vs:
                        if orchestrator.finished:
                            break
                        frame_count += 1
                        if frame_count % 30 == 1:
                            logger.info(
                                "[preflight] video frames consumed: %d", frame_count
                            )
                        try:
                            img_bgr = _to_bgr(frame)
                            orchestrator.on_video_frame(img_bgr)
                        except Exception as e:
                            logger.exception(
                                "[preflight] error processing video frame: %s", e
                            )
                except Exception as e:
                    logger.exception("[preflight] video consumption crashed: %s", e)

            tasks.add(asyncio.create_task(_consume_video()))
        elif track.kind == rtc.TrackKind.KIND_AUDIO:

            async def _consume_audio() -> None:
                try:
                    logger.info("[preflight] starting audio consumption")
                    # AudioStream is available on most livekit sdk builds.
                    stream_cls = getattr(rtc, "AudioStream", None)
                    if stream_cls is None:
                        logger.warning("rtc.AudioStream not available; skipping audio")
                        return
                    as_ = stream_cls(track)
                    chunk_count = 0
                    async for aframe in as_:
                        if orchestrator.finished:
                            break
                        chunk_count += 1
                        if chunk_count % 50 == 1:
                            logger.info(
                                "[preflight] audio chunks consumed: %d", chunk_count
                            )
                        try:
                            # AudioFrameEvent wrapper; extract .frame if needed
                            audio_frame = getattr(aframe, "frame", aframe)

                            # Try to_ndarray first (older SDK versions)
                            if hasattr(audio_frame, "to_ndarray"):
                                pcm = audio_frame.to_ndarray()
                            else:
                                # Newer SDK: use data property (int16 samples)
                                data = audio_frame.data
                                # AudioFrame.data is int16 samples
                                pcm = (
                                    np.frombuffer(data, dtype=np.int16).astype(
                                        np.float32
                                    )
                                    / 32768.0
                                )

                            pcm = _pcm_to_mono_float32(pcm)
                            sr = int(getattr(audio_frame, "sample_rate", 48000))
                            orchestrator.on_audio_pcm(pcm, sample_rate=sr)
                        except Exception as e:
                            logger.exception(
                                "[preflight] error processing audio chunk: %s", e
                            )
                except Exception as e:
                    logger.exception("[preflight] audio consumption crashed: %s", e)

            tasks.add(asyncio.create_task(_consume_audio()))

    try:
        logger.info(
            "[preflight] connecting to LiveKit room=%s session=%s",
            room_name,
            session_id,
        )
        await room.connect(LIVEKIT_URL, token)

        timeout = float(cfg.max_total_time_sec)
        if ANALYSIS_HARD_TIMEOUT_SEC and ANALYSIS_HARD_TIMEOUT_SEC > 0:
            timeout = min(timeout, float(ANALYSIS_HARD_TIMEOUT_SEC))

        await asyncio.wait_for(done.wait(), timeout=timeout)

    except asyncio.TimeoutError:
        logger.warning("preflight timed out; sending failure")
        last_state = orchestrator.get_last_state()
        await publish(
            {
                "type": "result",
                "passed": False,
                "failure_reason": "TIMEOUT",
                "ratios": last_state.get("ratios", {}),
                "scores": last_state.get("scores", {}),
                "flags": last_state.get("flags", []),
                # API 명세 필드
                "total_frames": last_state.get("total_frames", 0),
                "valid_frames": last_state.get("valid_frames", 0),
                "confidence": last_state.get("confidence", 0.0),
            }
        )
        result_status = "failure"
    except Exception as e:
        logger.exception("preflight error: %s", e)
        result_status = "failure"
        # Send error message to frontend
        with contextlib.suppress(Exception):
            await _publish_error(room, str(e), "INTERNAL_ERROR")
    finally:
        for t in list(tasks):
            if not t.done():
                t.cancel()
        with contextlib.suppress(Exception):
            await room.disconnect()

        if result_status:
            await notify_backend(room_name, result_status)
