# Fastapi 진입점.

# AI/services/pose-estimation/app/main.py
"""FastAPI 서버 (API 엔드포인트)"""

import io
import time
import argparse
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
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
        "device": str(model.device),
        "debug_mode": settings.DEBUG_MODE
    }


@app.post("/api/v1/pose/detect")
async def detect_pose(
    file: UploadFile = File(...),
    threshold: float = 0.3,
    visualize: bool = Query(False, description="스켈레톤 시각화 이미지 반환 (debug 모드에서만 동작)"),
    show_bbox: bool = True,     # 바운딩 박스
    show_keypoints: bool = True, # 키 포인트
    show_frame: bool = True # 스켈레톤
):
    """
    단일 이미지에서 자세 추정
    
    - file: 이미지 파일 (jpg, png 등)
    - threshold: 감지 신뢰도 임계값 (0.0 ~ 1.0)
    - visualize: 스켈레톤 시각화 이미지 반환 여부 (debug 모드에서만 동작)
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
        
        # 디버그 모드 + visualize 요청 시 이미지 반환
        if settings.DEBUG_MODE and visualize:
            from app.utils.visualize import draw_skeleton
            
            annotated_image = draw_skeleton(
                image, 
                results,
                keypoint_threshold=threshold,
                show_bbox=show_bbox,
                show_keypoints=show_keypoints,
                show_frame=show_frame
            )
                        
            # PIL -> bytes
            img_buffer = io.BytesIO()
            annotated_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            
            return StreamingResponse(
                img_buffer,
                media_type="image/png",
                headers={
                    "X-Processing-Time-Ms": str(round(processing_time, 2)),
                    "X-Person-Count": str(len(results))
                }
            )
        
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
    
    - image_url: 이미지 URL
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

    parser = argparse.ArgumentParser(description="ViTPose API Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    # 디버그 모드 설정
    if args.debug:
        settings.DEBUG_MODE = True
        print(" ✅ 디버그 모드 활성화 - 스켈레톤 시각화 가능")
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )