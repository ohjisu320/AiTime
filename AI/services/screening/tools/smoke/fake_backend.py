"""Fake backend for local smoke testing.

Starts a tiny FastAPI server that mimics the backend endpoint:
  POST /api/v1/screening/complete

It prints received payloads and keeps the last one in memory.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Fake Backend (Smoke Test)", version="0.1.0")


class ScreeningCompleteRequest(BaseModel):
    roomName: str
    status: str = "success"


LAST_COMPLETE: dict[str, Any] | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/screening/complete")
async def screening_complete(req: ScreeningCompleteRequest) -> dict[str, Any]:
    global LAST_COMPLETE
    payload = req.model_dump()
    payload["received_at"] = datetime.now(timezone.utc).isoformat()
    LAST_COMPLETE = payload
    print(f"[fake-backend] screening_complete: {payload}")
    return {
        "status": "200 OK",
        "message": "스크리닝 완료 처리되었습니다. (fake backend)",
        "data": None,
        "code": 200,
    }


@app.get("/api/v1/screening/complete/last")
async def last_complete() -> dict[str, Any]:
    return {"last": LAST_COMPLETE}
