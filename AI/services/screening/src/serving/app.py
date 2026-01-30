from __future__ import annotations

from fastapi import FastAPI
from src.serving.webrtc import router as webrtc_router

app = FastAPI(title="Preflight Screening (WebRTC)")

app.include_router(webrtc_router, prefix="/webrtc")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
