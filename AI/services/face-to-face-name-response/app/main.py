import logging
import os
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.rtn.service.engine import build_engine

# 업로드 허용 확장자 (필요시 추가)
ALLOWED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# (선택) 업로드 최대 용량 제한 (예: 300MB)
MAX_UPLOAD_BYTES = 300 * 1024 * 1024

logger = logging.getLogger("RTNAnalyzer")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# 엔진/디버그 라우터 생성 (mjpeg 켤 거면 True)
engine, debug_router = build_engine(enable_mjpeg=True, debug=False)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # startup: 모델/분석기 선로딩
    if getattr(engine, "analyzer", None) is None and hasattr(engine, "get_analyzer"):
        engine.get_analyzer()
    yield
    # shutdown: 필요 시 정리 로직 추가 가능


app = FastAPI(title="rtn-eyecontact-service", lifespan=lifespan)


if debug_router is not None:
    app.include_router(debug_router)


class AnalyzeRequest(BaseModel):
    video_path: str


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "rtn-eyecontact-service is running. Go to /docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "I'm Okay, and you?"}


def _analyze_sync(video_path: str) -> dict[str, Any]:
    analyzer = engine.analyzer
    return analyzer.analyze(video_path)


@app.post("/analyze")
async def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    """
    서버 로컬 경로에 있는 비디오를 분석 (예: EC2 내부 경로)
    """
    if not os.path.exists(req.video_path):
        raise HTTPException(
            status_code=400,
            detail=f"video_path not found: {req.video_path}",
        )

    # 오래 걸리는 분석은 threadpool로 빼기 (event loop block 방지)
    result = await run_in_threadpool(_analyze_sync, req.video_path)
    return result


UPLOAD_FILE_DEFAULT: Any = File(...)


@app.post("/analyze/upload")
async def analyze_upload(file: UploadFile = UPLOAD_FILE_DEFAULT) -> dict[str, Any]:
    """
    사용자가 업로드한 비디오 파일을 임시 저장 후 분석
    """
    filename = file.filename or "uploaded.mp4"
    suffix = os.path.splitext(filename)[-1].lower() or ".mp4"

    # 확장자 검사
    if suffix not in ALLOWED_VIDEO_EXTS:
        allowed = ", ".join(sorted(ALLOWED_VIDEO_EXTS))
        raise HTTPException(
            status_code=400,
            detail=(f"unsupported file type: {suffix} (allowed: [{allowed}])"),
        )

    tmp_path: str | None = None
    total: int = 0

    try:
        # 임시 파일로 스트리밍 저장 (큰 파일도 안전)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name

            while True:
                chunk = await file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break

                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"file too large (max {MAX_UPLOAD_BYTES} bytes)",
                    )

                tmp.write(chunk)

        # 분석 실행
        result = await run_in_threadpool(_analyze_sync, tmp_path)
        return result

    finally:
        if tmp_path:
            with suppress(FileNotFoundError):
                os.remove(tmp_path)
