import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel
from src.contracts.context import ROI
from src.serving.livekit_runner import run_preflight_livekit

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalysisStartRequest(BaseModel):
    room_name: str
    token: str
    session_id: int
    participant_name: str

    # optional: allow backend/client to override ROI config
    roi_1: ROI | None = None
    roi_2: ROI | None = None

    # optional: free-form client metadata (UA, device model, etc.)
    client_info: dict[str, Any] = {}


# Track running analyses so backend can avoid double-start.
ACTIVE_TASKS: dict[int, asyncio.Task] = {}


@router.post("/analysis/start")
async def start_analysis(
    body: AnalysisStartRequest, request: Request
) -> dict[str, Any]:
    """Backend -> AI: start screening analysis.

    Returns immediately and runs the LiveKit join+analysis in the background.
    """

    if body.session_id in ACTIVE_TASKS and not ACTIVE_TASKS[body.session_id].done():
        return {
            "status": "already_running",
            "room_name": body.room_name,
            "session_id": body.session_id,
        }

    repro = {
        "code_sha": request.headers.get("x-code-sha", "unknown"),
        "config_version": request.headers.get("x-config-version", "unknown"),
        "env_lock_hash": request.headers.get("x-env-lock-hash", "unknown"),
        "trace_id": request.headers.get("x-trace-id", f"preflight_{body.session_id}"),
    }

    task = asyncio.create_task(
        run_preflight_livekit(
            room_name=body.room_name,
            token=body.token,
            session_id=body.session_id,
            participant_name=body.participant_name,
            roi_1=body.roi_1,
            roi_2=body.roi_2,
            client_info=body.client_info,
            repro_overrides=repro,
        )
    )

    ACTIVE_TASKS[body.session_id] = task

    def _cleanup(_: asyncio.Task) -> None:
        ACTIVE_TASKS.pop(body.session_id, None)

    task.add_done_callback(_cleanup)

    logger.info(
        "analysis started session_id=%s room=%s", body.session_id, body.room_name
    )
    return {
        "status": "started",
        "room_name": body.room_name,
        "session_id": body.session_id,
        "message": "Analysis started successfully",
    }


@router.get("/analysis/active")
async def list_active() -> dict[str, Any]:
    """(Optional) quick health visibility for ops."""
    return {
        "active_sessions": sorted(
            [sid for sid, t in ACTIVE_TASKS.items() if not t.done()]
        ),
        "count": sum(1 for t in ACTIVE_TASKS.values() if not t.done()),
    }
