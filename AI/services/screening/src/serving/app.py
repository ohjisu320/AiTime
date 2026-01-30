import logging

from fastapi import FastAPI
from src.serving.admin import router as admin_router
from src.serving.webrtc import router as webrtc_router
from starlette.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(title="Preflight Screening (WebRTC)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "null",  # file:// 로 열었을 때 (브라우저에 따라 동작 달라질 수 있음)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webrtc_router, prefix="/webrtc")
app.include_router(admin_router, prefix="/admin")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
