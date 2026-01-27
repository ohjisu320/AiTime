# Fastapi 진입점.

# AI/services/pose-estimation/app/main.py
"""FastAPI 서버 (API 엔드포인트)"""

# ============================================================================
# 1. IMPORTS
# ============================================================================
import os
import io
import time
import base64
import shutil
import tempfile
import argparse
from enum import Enum
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

from app.config import settings
from app.models.vitpose import get_model
# MotionAnalyzer는 lazy loading으로 처리 (아래 get_analyzer 함수)


# ============================================================================
# 2. ENUMS & TYPES
# ============================================================================
class ResponseType(str, Enum):
    """응답 타입"""
    JSON = "json"    # JSON 분석 결과만
    VIDEO = "video"  # 스켈레톤 영상만
    FULL = "full"    # JSON + 영상 (Base64)

# ============================================================================
# 3. LAZY LOADERS (Pipeline은 나중에 로드)
# ============================================================================
# 전역 분석기 인스턴스
_analyzer = None

# lazy loading 으로
def get_analyzer():
    """MotionAnalyzer 지연 로딩 (구현 안 됐으면 None 반환)"""
    global _analyzer
    if _analyzer is None:
        try:
            from app.pipeline.analyzer import MotionAnalyzer
            _analyzer = MotionAnalyzer()
            print("✅ MotionAnalyzer 성공적으로 로드됨")
        except Exception as e:
            print(f" MotionAnalyzer 아직 준비 안됨: {e}")
            return None
    return _analyzer

# ============================================================================
# 4. APP SETUP
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행"""
    print("✅ FastAPI 서버 실행 중...")
    print(f"🐛 Debug mode: {settings.DEBUG_MODE}")
    get_model()  # Pose 모델 미리 로딩
    yield
    print("✅ 서버 종료 중...")


app = FastAPI(
    title="ViTPose Worker API",
    description="Human Pose Estimation & Motion Analysis Service",
    version="0.2.0",
    lifespan=lifespan
)

# ============================================================================
# 5. HEALTH & INFO ENDPOINTS
# ============================================================================
@app.get("/health")
async def health_check():
    """헬스 체크"""
    model = get_model()
    analyzer = get_analyzer()
    
    return {
        "status": "healthy",
        "device": str(model.device),
        "debug_mode": settings.DEBUG_MODE,
        "motion_analyzer_available": analyzer is not None
    }


@app.get("/api/v1/motion/actions")
async def list_actions():
    """지원하는 동작 목록"""
    return {
        "actions": [
            {"name": "clapping", "description": "손뼉 치기", "age_range": "12-17개월"},
            {"name": "hurray", "description": "만세 동작", "age_range": "12-17개월"},
            {"name": "walking_back", "description": "뒷걸음질", "age_range": "12-17개월"},
            {"name": "jumping", "description": "제자리 뛰기", "age_range": "18-23개월"},
            {"name": "kicking", "description": "공 차는 자세", "age_range": "18-23개월"},
            {"name": "throwing", "description": "머리 위로 공 던지기", "age_range": "18-23개월"},
        ]
    }


# ============================================================================
# 6. POSE DETECTION ENDPOINTS (이미지)
# ============================================================================
@app.post("/api/v1/pose/detect")
async def detect_pose(
    file: UploadFile = File(...),
    threshold: float = 0.3,
    visualize: bool = Query(False, description="스켈레톤 시각화 이미지 반환"),
    show_bbox: bool = True,
    show_keypoints: bool = True,
    show_frame: bool = True
):
    """단일 이미지에서 자세 추정"""
    start_time = time.time()
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        model = get_model()
        results = model.detect(image, threshold)
        
        processing_time = (time.time() - start_time) * 1000
        
        # 디버그 모드 + visualize 시 이미지 반환
        if settings.DEBUG_MODE and visualize:
            from app.utils.visualize import draw_skeleton
            
            annotated_image = draw_skeleton(
                image, results,
                keypoint_threshold=threshold,
                show_bbox=show_bbox,
                show_keypoints=show_keypoints,
                show_frame=show_frame
            )
            
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
    """URL에서 이미지 다운로드 후 자세 추정"""
    import requests
    
    start_time = time.time()
    
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        
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


# ============================================================================
# 7. MOTION ANALYSIS ENDPOINTS (영상 파이프라인)
# ============================================================================
@app.post("/api/v1/motion/analyze")
async def analyze_motion(
    # === 필수 파라미터 ===
    video: UploadFile = File(..., description="분석할 영상 파일 (mp4, webm)"),
    action_type: str = Form(..., description="동작 유형 (hurray, clapping 등)"),
    age_months: int = Form(..., description="아동 월령 (12-36)"),
    
    # === 옵션 파라미터 ===
    use_parent_reference: bool = Form(default=False, description="부모 동작을 기준으로 비교"),
    identify_roles: bool = Form(default=True, description="부모/아이 역할 자동 구분"),
    smooth: bool = Form(default=True, description="스무딩 적용 (노이즈 감소)"),
    smooth_method: str = Form(default="one_euro", description="스무딩 방법"),
    
    # === 응답 타입 ===
    response_type: ResponseType = Query(
        default=ResponseType.JSON,
        description="응답 타입: json(분석결과), video(영상), full(둘다)"
    )
):
    """
    동작 모방행동 분석 API
    
    **응답 타입:**
    - `json`: 분석 결과 JSON만 반환 (기본값)
    - `video`: 스켈레톤 시각화 영상만 반환 (mp4)
    - `full`: JSON + 영상 모두 반환 (영상은 Base64 인코딩)
    
    **필수 파라미터:**
    - video: 영상 파일 (mp4, webm)
    - action_type: 동작 유형 (hurray, clapping, jumping 등)
    - age_months: 아동 월령 (12-36개월)
    
    **옵션 파라미터:**
    - use_parent_reference: 부모 동작을 기준으로 비교 (True/False)
    - identify_roles: 부모/아이 자동 구분 (True/False)
    - smooth: 스무딩 적용 (True/False)
    - smooth_method: 스무딩 방법 (one_euro, exponential, moving_avg)
    """
    from app.pipeline.exceptions import InvalidInputError, ReferenceNotFoundError
    
    # Pipeline 사용 가능 여부 확인
    motion_analyzer = get_analyzer()
    if motion_analyzer is None:
        raise HTTPException(
            status_code=503,
            detail="Motion analyzer not available. Pipeline modules are not fully implemented yet."
        )
    
    tmp_path = None
    output_dir = None
    
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            contents = await video.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # 응답 타입에 따라 처리
        if response_type == ResponseType.JSON:
            # === JSON만 반환 ===
            result = motion_analyzer.analyze(
                video_path=tmp_path,
                action_type=action_type,
                age_months=age_months,
                use_parent_reference=use_parent_reference,
                identify_roles=identify_roles,
                smooth=smooth,
                smooth_method=smooth_method
            )
            
            response_data = {
                "status": "success",
                **result.to_dict()
            }
            return JSONResponse(content=response_data)
        
        else:
            # === VIDEO 또는 FULL: 시각화 포함 분석 ===
            output_dir = tempfile.mkdtemp(prefix="motion_viz_")
            
            result = motion_analyzer.analyze_with_visualization(
                video_path=tmp_path,
                action_type=action_type,
                age_months=age_months,
                output_folder=output_dir,
                save_skeleton_video=True,
                use_parent_reference=use_parent_reference,
                identify_roles=identify_roles,
                smooth=smooth,
                smooth_method=smooth_method
            )
            
            video_path = Path(output_dir) / "skeleton_video.mp4"
            
            if not video_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate visualization video"
                )
            
            if response_type == ResponseType.VIDEO:
                # === 영상만 반환 ===
                # 영상을 메모리로 읽어서 반환 (임시 파일 정리를 위해)
                with open(video_path, "rb") as f:
                    video_bytes = f.read()
                
                return StreamingResponse(
                    io.BytesIO(video_bytes),
                    media_type="video/mp4",
                    headers={
                        "Content-Disposition": f'attachment; filename="analysis_{action_type}.mp4"',
                        "X-Analysis-Passed": str(result.passed),
                        "X-Similarity-Score": f"{result.similarity_score:.4f}",
                        "X-Reaction-Delay-Sec": f"{result.reaction_delay_sec:.2f}",
                        "X-Processing-Time-Sec": f"{result.processing_time_sec:.2f}"
                    }
                )
            
            else:  # ResponseType.FULL
                # === JSON + 영상 (Base64) ===
                with open(video_path, "rb") as f:
                    video_base64 = base64.b64encode(f.read()).decode("utf-8")
                
                response_data = {
                    "status": "success",
                    **result.to_dict(),
                    "visualization": {
                        "video_base64": video_base64,
                        "format": "mp4",
                        "filename": f"analysis_{action_type}.mp4"
                    }
                }
                return JSONResponse(content=response_data)
    
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ReferenceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 임시 파일 정리
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if output_dir and os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)


# ============================================================================
# 8. MAIN (CLI)
# ============================================================================
if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="ViTPose API Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    if args.debug:
        settings.DEBUG_MODE = True
        print("✅ 디버그 모드 활성화 - 스켈레톤 시각화 가능")
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )