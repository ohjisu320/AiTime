# services/name_non_facing/app/pipeline/stages/head_detect_stage.py
"""
머리 탐지 Stage (YOLO Head)

비디오 프레임에서 머리를 탐지하고, 부모/아이를 구분합니다.
MediaPipe와 달리 뒤통수도 탐지 가능합니다.

설계 의도:
    1. YOLO로 머리/사람 탐지 (360°)
    2. 부모/아이 구분 (bbox 크기 기준)
    3. 위치 벡터 생성

Reference:
    - 1409_뒤통수_미탐지문제로_yolohead및6drepnet360 모델 조합으로 변경.md
"""

from typing import Optional
import logging

import numpy as np

from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.context import PipelineContext
from app.models.head_detector import HeadDetector
from app.utils.video import extract_frames
from app.core.gaze_calculator import compute_position_vector_2d
from app.config import get_settings

logger = logging.getLogger(__name__)


class HeadDetectStage(BaseStage):
    """
    머리 탐지 Stage (YOLO 기반)
    
    비디오 프레임에서 부모/아이 머리를 탐지하고 위치 벡터를 생성합니다.
    
    Input:
        - context.video_path: 비디오 파일 경로
        
    Output:
        - context.frames: 프레임 이미지 목록
        - context.frame_timestamps: 프레임 타임스탬프 목록
        - context.head_detections: 프레임별 머리 탐지 결과
        - context.parent_positions: 시간별 부모 위치
        - context.child_detections: 시간별 아이 탐지 결과
        - context.is_first_person_view: 1인칭 모드 여부
    """
    
    def __init__(self, detector: HeadDetector = None, target_fps: int = None):
        """
        Args:
            detector: 머리 탐지기 (None이면 자동 생성)
            target_fps: 프레임 추출 FPS (None이면 config 값 사용)
        """
        self._settings = get_settings()
        self._detector = detector or HeadDetector()
        self._target_fps = target_fps
    
    @property
    def name(self) -> str:
        return "HeadDetectStage"
    
    def _assign_by_reference(
        self,
        detections: list,
        parent_ref: tuple,
        child_ref: tuple,
        frame_width: int,
        frame_height: int
    ) -> tuple:
        """
        기준 위치를 기반으로 부모/아이 할당
        
        Args:
            detections: HeadDetection 목록
            parent_ref: 부모 기준 위치 (cx, cy) 픽셀
            child_ref: 아이 기준 위치 (cx, cy) 픽셀
            frame_width: 프레임 너비
            frame_height: 프레임 높이
            
        Returns:
            (parent_detection, child_detection)
        """
        if len(detections) == 0:
            return None, None
        
        if len(detections) == 1:
            # 1개면 아이로 가정
            det = detections[0]
            det.person_type = "child"
            return None, det
        
        # 각 detection과 기준 위치의 거리 계산
        parent_distances = []
        child_distances = []
        
        for det in detections:
            cx, cy = det.center_pixel(frame_width, frame_height)
            
            parent_dist = np.sqrt((cx - parent_ref[0])**2 + (cy - parent_ref[1])**2)
            child_dist = np.sqrt((cx - child_ref[0])**2 + (cy - child_ref[1])**2)
            
            parent_distances.append((det, parent_dist))
            child_distances.append((det, child_dist))
        
        # 부모: parent_ref에 가장 가까운 것
        parent_det = min(parent_distances, key=lambda x: x[1])[0]
        parent_det.person_type = "parent"
        
        # 아이: child_ref에 가장 가까운 것 (부모와 중복 방지)
        child_candidates = [(d, dist) for d, dist in child_distances if d is not parent_det]
        if child_candidates:
            child_det = min(child_candidates, key=lambda x: x[1])[0]
            child_det.person_type = "child"
        else:
            child_det = None
        
        return parent_det, child_det
    
    def validate(self, context: PipelineContext) -> Optional[str]:
        """비디오 파일 존재 여부 검증"""
        from pathlib import Path
        if not Path(context.video_path).exists():
            return f"비디오 파일이 존재하지 않습니다: {context.video_path}"
        return None
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """
        머리 탐지 및 위치 벡터 생성
        
        Process:
            1. 비디오에서 프레임 추출 (FPS 샘플링)
            2. 각 프레임에서 YOLO로 머리 탐지
            3. 부모/아이 구분
            4. 위치 벡터 생성
        """
        # 1. 프레임 추출
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
        
        # 2. 프레임별 머리 탐지 + 전역 분석 (3-pass)
        head_detections = {}        # {timestamp: [HeadDetection]}
        parent_positions = []       # [(timestamp, (cx, cy))]
        child_detections = []       # [(timestamp, HeadDetection or None)]
        position_vectors = []       # [(timestamp, np.ndarray)]
        
        first_person_count = 0
        no_child_count = 0
        
        # ===== Pass 1: 전체 프레임 탐지 + 초기 판단 =====
        initial_assignments = []  # [(timestamp, detections, parent_det, child_det)]
        
        import time
        pass1_start = time.time()
        logger.info("🔍 Pass 1: 전체 프레임 탐지 및 초기 판단")
        for i, (frame, ts) in enumerate(zip(frames, timestamps)):
            detections = self._detector.detect(frame)
            head_detections[ts] = detections
            
            parent_pos, child, parent_det = self._detector.identify_parent_child(
                detections=detections,
                frame_shape=frame.shape
            )
            
            initial_assignments.append((ts, detections, parent_det, child))
        
        pass1_time = time.time() - pass1_start
        logger.info(f"✅ Pass 1 완료: {pass1_time:.2f}s")
        
        # ===== Pass 2: 영역별 성향 분석 (클러스터링 + Outlier 필터링) =====
        pass2_start = time.time()
        logger.info("📊 Pass 2: 영역별 판단 성향 분석")
        
        # 모든 detection의 위치와 판단 결과 수집
        all_child_positions = []
        all_parent_positions = []
        
        for ts, detections, parent_det, child in initial_assignments:
            if child:
                cx, cy = child.center_pixel(video_info.width, video_info.height)
                all_child_positions.append((cx, cy))
            if parent_det:
                cx, cy = parent_det.center_pixel(video_info.width, video_info.height)
                all_parent_positions.append((cx, cy))
        
        # Outlier 필터링 (IQR 방식)
        def remove_outliers(positions, threshold=1.5):
            if len(positions) < 4:
                return positions
            x_vals = [p[0] for p in positions]
            y_vals = [p[1] for p in positions]
            
            def filter_axis(vals):
                q1, q3 = np.percentile(vals, [25, 75])
                iqr = q3 - q1
                lower = q1 - threshold * iqr
                upper = q3 + threshold * iqr
                return lower, upper
            
            x_lower, x_upper = filter_axis(x_vals)
            y_lower, y_upper = filter_axis(y_vals)
            
            filtered = [
                (x, y) for x, y in positions
                if x_lower <= x <= x_upper and y_lower <= y <= y_upper
            ]
            return filtered if filtered else positions
        
        all_child_positions = remove_outliers(all_child_positions)
        all_parent_positions = remove_outliers(all_parent_positions)
        
        # 부모 감지율 로깅
        parent_detection_ratio = len(all_parent_positions) / len(frames) if frames else 0
        logger.info(f"🎥 부모 감지율: {parent_detection_ratio*100:.1f}% ({len(all_parent_positions)}/{len(frames)}프레임)")
        
        # 기준 위치 계산 (중앙값 사용 - outlier에 강건)
        child_ref_center = None
        parent_ref_center = None
        
        if all_child_positions:
            child_ref_center = (
                float(np.median([p[0] for p in all_child_positions])),
                float(np.median([p[1] for p in all_child_positions]))
            )
            logger.info(f"👶 아이 영역 중심: ({child_ref_center[0]:.0f}, {child_ref_center[1]:.0f}) "
                       f"(총 {len(all_child_positions)}회 탐지, outlier 제거 후)")
        
        if all_parent_positions:
            parent_ref_center = (
                float(np.median([p[0] for p in all_parent_positions])),
                float(np.median([p[1] for p in all_parent_positions]))
            )
            logger.info(f"👨 부모 영역 중심: ({parent_ref_center[0]:.0f}, {parent_ref_center[1]:.0f}) "
                       f"(총 {len(all_parent_positions)}회 탐지, outlier 제거 후)")
        
        pass2_time = time.time() - pass2_start
        logger.info(f"✅ Pass 2 완료: {pass2_time:.2f}s")
        
        # ===== Pass 3: 영역 기반 재할당 + Smoothing =====
        pass3_start = time.time()
        logger.info("🎯 Pass 3: 영역 기반 재할당 및 smoothing")
        
        # Smoothing용 버퍼
        parent_pos_buffer = []
        child_pos_buffer = []
        SMOOTH_WINDOW = 5  # 이동 평균 윈도우 크기 (더 큰 값 = 더 부드러운 추적)
        
        for i, (ts, detections, _, _) in enumerate(initial_assignments):
            # 영역 기반 재할당
            if parent_ref_center and child_ref_center and len(detections) >= 2:
                # 2명 이상: 기준점 기반 할당
                parent_det, child = self._assign_by_reference(
                    detections, parent_ref_center, child_ref_center,
                    video_info.width, video_info.height
                )
                if parent_det:
                    parent_pos_raw = parent_det.center_pixel(video_info.width, video_info.height)
                else:
                    parent_pos_raw = parent_ref_center  # 부모 탐지 실패 시 기준점 사용
            elif parent_ref_center and len(detections) == 1:
                # 1명만 탐지 + 부모 기준점 존재: 탐지된 것을 아이로, 부모는 기준점
                child = detections[0]
                child.person_type = "child"
                parent_pos_raw = parent_ref_center
            elif child_ref_center and len(detections) == 1:
                # 1명만 탐지 + 아이 기준점만 존재: 기존 로직
                parent_pos_raw, child, parent_det = self._detector.identify_parent_child(
                    detections=detections,
                    frame_shape=frame.shape
                )
            else:
                # 기준점 없음: 기존 로직 (초기 할당)
                parent_pos_raw, child, parent_det = self._detector.identify_parent_child(
                    detections=detections,
                    frame_shape=frame.shape
                )
            
            # 부모 위치 Smoothing
            parent_pos_buffer.append(parent_pos_raw)
            if len(parent_pos_buffer) > SMOOTH_WINDOW:
                parent_pos_buffer.pop(0)
            
            parent_pos = (
                np.mean([p[0] for p in parent_pos_buffer]),
                np.mean([p[1] for p in parent_pos_buffer])
            )
            
            parent_positions.append((ts, parent_pos))
            child_detections.append((ts, child))
            
            # 1인칭 모드 카운트
            if len(detections) <= 1:
                first_person_count += 1
            
            if child is None:
                no_child_count += 1
            else:
                # 아이 위치 Smoothing
                child_center_raw = child.center_pixel(
                    video_info.width, video_info.height
                )
                child_pos_buffer.append(child_center_raw)
                if len(child_pos_buffer) > SMOOTH_WINDOW:
                    child_pos_buffer.pop(0)
                
                child_center = (
                    np.mean([p[0] for p in child_pos_buffer]),
                    np.mean([p[1] for p in child_pos_buffer])
                )
                
                # 위치 벡터 계산 (smoothed 위치 사용)
                pos_vec = compute_position_vector_2d(
                    child_center=child_center,
                    parent_center=parent_pos,
                    frame_shape=(video_info.height, video_info.width)
                )
                position_vectors.append((ts, pos_vec))
        
        pass3_time = time.time() - pass3_start
        total_time = pass1_time + pass2_time + pass3_time
        logger.info(f"✅ Pass 3 완료: {pass3_time:.2f}s")
        logger.info(f"⏱️ 전체 처리 시간: {total_time:.2f}s (Pass1: {pass1_time:.2f}s, Pass2: {pass2_time:.2f}s, Pass3: {pass3_time:.2f}s)")
        
        # 3. 컨텍스트에 저장
        context.head_detections = head_detections
        context.parent_positions = parent_positions
        context.child_detections = child_detections
        context.position_vectors = position_vectors
        
        # 1인칭 모드 판정
        # FIRST_PERSON_FALLBACK=False (기본값): 자동 1인칭 전환 비활성화
        # FIRST_PERSON_FALLBACK=True (CLI --selfie 등): 부모 미감지 시 1인칭 허용
        if not self._settings.FIRST_PERSON_FALLBACK:
            # 자동 1인칭 전환 비활성화 (기본 동작)
            context.is_first_person_view = False
            if parent_ref_center is None and parent_detection_ratio == 0:
                logger.warning(
                    "⚠️ 부모 미감지 (0%), 부모 기준점 없음. "
                    "1인칭 모드가 필요하면 --selfie 옵션 또는 "
                    "FIRST_PERSON_FALLBACK=True 설정을 사용하세요."
                )
        else:
            # FIRST_PERSON_FALLBACK=True: 기존 자동 판정 로직
            if parent_ref_center is not None:
                # 부모 기준점 존재 → 3인칭
                context.is_first_person_view = False
            else:
                # 부모 기준점 없음 → 1인칭
                context.is_first_person_view = first_person_count > len(frames) / 2
        
        # 4. 결과 로깅
        child_detected_count = len(frames) - no_child_count
        
        logger.info(
            f"👤 머리 탐지 완료: "
            f"아이 탐지 {child_detected_count}/{len(frames)}프레임 "
            f"({child_detected_count/len(frames)*100:.1f}%)"
        )
        
        if context.is_first_person_view:
            logger.info("📱 1인칭 모드 활성화 (부모 = 카메라 중앙)")
        elif parent_ref_center is not None:
            logger.info(f"👨 부모 위치: 기준점 ({parent_ref_center[0]:.0f}, {parent_ref_center[1]:.0f}) 사용")
        
        if no_child_count == len(frames):
            context.add_warning(
                self.name,
                "모든 프레임에서 아이 머리 미탐지"
            )
        
        return context
