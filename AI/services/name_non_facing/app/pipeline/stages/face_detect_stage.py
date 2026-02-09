# services/name_non_facing/app/pipeline/stages/face_detect_stage.py
"""
얼굴 탐지 Stage

비디오 프레임에서 얼굴을 탐지하고, 부모/아이를 구분합니다.

설계 의도:
    1. 부모/아이 위치 식별
       - 2명 탐지: bbox 크기로 구분 (큰 쪽 = 부모)
       - 1명 탐지: 1인칭 모드 (부모 = 카메라 중앙)
       
    2. 위치 벡터 생성
       - 아이 얼굴 중심 → 부모 얼굴 중심 방향 벡터
       
    3. 효율적 프레임 처리
       - FPS 샘플링으로 연산량 감소

Reference:
    - 1318_구현설계.md: 부모/아이 구분 전략
"""

from typing import Optional
import logging

from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.context import PipelineContext
from app.models.face_detector import FaceDetector
from app.utils.video import extract_frames
from app.core.vector_math import compute_position_vector_3d
from app.config import get_settings

logger = logging.getLogger(__name__)


class FaceDetectStage(BaseStage):
    """
    얼굴 탐지 Stage
    
    비디오 프레임에서 부모/아이 얼굴을 탐지하고 위치 벡터를 생성합니다.
    
    Input:
        - context.video_path: 비디오 파일 경로
        
    Output:
        - context.frames: 프레임 이미지 목록
        - context.frame_timestamps: 프레임 타임스탬프 목록
        - context.face_detections: 프레임별 얼굴 탐지 결과
        - context.parent_positions: 시간별 부모 위치
        - context.child_detections: 시간별 아이 탐지 결과
        - context.is_first_person_view: 1인칭 모드 여부
    """
    
    def __init__(self, detector: FaceDetector = None, target_fps: int = None):
        """
        Args:
            detector: 얼굴 탐지기 (None이면 자동 생성)
            target_fps: 프레임 추출 FPS (None이면 config 값 사용, 원본 FPS 유지하려면 0 또는 높은 값)
        """
        self._settings = get_settings()
        self._detector = detector or FaceDetector()
        self._target_fps = target_fps
    
    @property
    def name(self) -> str:
        return "FaceDetectStage"
    
    def validate(self, context: PipelineContext) -> Optional[str]:
        """비디오 파일 존재 여부 검증"""
        from pathlib import Path
        if not Path(context.video_path).exists():
            return f"비디오 파일이 존재하지 않습니다: {context.video_path}"
        return None
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        얼굴 탐지 및 위치 벡터 생성
        
        Process:
            1. 비디오에서 프레임 추출 (FPS 샘플링)
            2. 각 프레임에서 얼굴 탐지
            3. 부모/아이 구분
            4. 위치 벡터 생성
        """
        # 1. 프레임 추출
        # target_fps: None이면 config 값, 0이면 원본 FPS
        fps_to_use = self._target_fps if self._target_fps is not None else self._settings.VIDEO_FPS_SAMPLE
        logger.info(f"🎬 프레임 추출 시작 (Target FPS: {fps_to_use or '원본'})")
        
        frames, timestamps, video_info = extract_frames(
            video_path=context.video_path,
            target_fps=fps_to_use if fps_to_use else None
        )
        
        context.frames = frames
        context.frame_timestamps = timestamps
        context.original_fps = video_info.fps
        context.frame_width = video_info.width
        context.frame_height = video_info.height
        
        logger.info(
            f"🎬 프레임 추출 완료: {len(frames)}개 "
            f"({video_info.width}x{video_info.height}, "
            f"원본 {video_info.fps:.1f}fps)"
        )
        
        # 2. 프레임별 얼굴 탐지
        face_detections = {}        # {timestamp: [FaceDetection]}
        parent_positions = []       # [(timestamp, (cx, cy))]
        child_detections = []       # [(timestamp, FaceDetection or None)]
        position_vectors = []       # [(timestamp, Vector3D)]
        
        first_person_count = 0
        no_child_count = 0
        
        for i, (frame, ts) in enumerate(zip(frames, timestamps)):
            # 얼굴 탐지
            detections = self._detector.detect(frame)
            face_detections[ts] = detections
            
            # 부모/아이 구분
            parent_pos, child = self._detector.identify_parent_child(
                detections=detections,
                frame_shape=frame.shape
            )
            
            parent_positions.append((ts, parent_pos))
            child_detections.append((ts, child))
            
            # 1인칭 모드 카운트
            if len(detections) <= 1:
                first_person_count += 1
            
            if child is None:
                no_child_count += 1
            else:
                # 위치 벡터 계산
                child_center = child.center_pixel(
                    video_info.width, video_info.height
                )
                pos_vec = compute_position_vector_3d(
                    child_center=child_center,
                    parent_center=parent_pos
                )
                position_vectors.append((ts, pos_vec))
        
        # 3. 컨텍스트에 저장
        context.face_detections = face_detections
        context.parent_positions = parent_positions
        context.child_detections = child_detections
        context.position_vectors = position_vectors
        
        # 1인칭 모드 판정
        # FIRST_PERSON_FALLBACK=False(기본): 자동 전환 비활성화
        settings = get_settings()
        if not settings.FIRST_PERSON_FALLBACK:
            context.is_first_person_view = False
        else:
            context.is_first_person_view = first_person_count > len(frames) / 2
        
        # 4. 결과 로깅
        child_detected_count = len(frames) - no_child_count
        
        logger.info(
            f"🩷 얼굴 탐지 완료: "
            f"아이 탐지 {child_detected_count}/{len(frames)}프레임 "
            f"({child_detected_count/len(frames)*100:.1f}%)"
        )
        
        if context.is_first_person_view:
            logger.info("🩷 1인칭 모드 활성화 (부모 = 카메라 중앙)")
        
        if no_child_count == len(frames):
            context.add_warning(
                self.name,
                "모든 프레임에서 아이 얼굴 미탐지"
            )
        
        return context
