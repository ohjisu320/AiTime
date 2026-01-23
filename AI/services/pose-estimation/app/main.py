# Fastapi 진입점.

# app/main.py
"""FastAPI 서버 (API 엔드포인트)"""

import io
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image

from app.config import settings
from app.models.vitpose import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행"""
    # Startup: 모델 미리 로딩
    print("✅ FastAPI 서버 실행 중...")
    get_model()
    yield
    # Shutdown
    print(" ✅ 서버 종료 중...")


app = FastAPI(
    title="ViTPose Worker API",
    description="Human Pose Estimation Service",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """헬스 체크"""
    model = get_model()
    return {
        "status": "healthy",
        "device": str(model.device)
    }


@app.post("/api/v1/pose/detect")
async def detect_pose(
    file: UploadFile = File(...),
    threshold: float = 0.3
):
    """
    단일 이미지에서 자세 추정
    
    - **file**: 이미지 파일 (jpg, png 등)
    - **threshold**: 감지 신뢰도 임계값 (0.0 ~ 1.0)
    """
    start_time = time.time()
    
    try:
        # 이미지 로드
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 추론
        model = get_model()
        results = model.detect(image, threshold)
        
        processing_time = (time.time() - start_time) * 1000
        
        return JSONResponse(content={
            "status": "success",
            "processing_time_ms": round(processing_time, 2),
            "person_count": len(results),
            "results": results
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pose/detect-url")
async def detect_pose_from_url(
    image_url: str,
    threshold: float = 0.3
):
    """
    URL에서 이미지 다운로드 후 자세 추정
    
    - **image_url**: 이미지 URL
    - **threshold**: 감지 신뢰도 임계값
    """
    import requests
    
    start_time = time.time()
    
    try:
        # 이미지 다운로드
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        
        # 추론
        model = get_model()
        results = model.detect(image, threshold)
        
        processing_time = (time.time() - start_time) * 1000
        
        return JSONResponse(content={
            "status": "success",
            "processing_time_ms": round(processing_time, 2),
            "person_count": len(results),
            "results": results
        })
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)