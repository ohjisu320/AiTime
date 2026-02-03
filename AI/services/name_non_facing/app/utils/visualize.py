# services/name_non_facing/app/utils/visualize.py
"""
비디오 시각화 유틸리티

파이프라인 결과를 비디오에 오버레이하여 모니터링 및 디버깅을 지원합니다.

주요 기능:
    - YOLO Head bounding box 표시
    - Head Pose (yaw/pitch/roll) 시각화
    - 시선 벡터 및 위치 벡터 화살표
    - 오디오 이벤트 타임라인
    - Trial 결과 패널
    
Reference:
    - docs/1800_비디오_시각화_구현계획.md
"""

from typing import List, Tuple, Optional
from pathlib import Path
import logging

import numpy as np
import cv2

from app.pipeline.context import PipelineContext
from app.models.head_detector import HeadDetection
from app.models.head_pose_6d import HeadPose6D

logger = logging.getLogger(__name__)


# 컬러 스킴 (BGR)
COLOR_PARENT = (0, 255, 0)      # 초록 - 부모
COLOR_CHILD = (255, 0, 0)       # 파랑 - 아이
COLOR_GAZE = (0, 255, 255)      # 노랑 - 시선 벡터
COLOR_POSITION = (255, 255, 0)  # 하늘 - 위치 벡터
COLOR_NAME_CALL = (0, 165, 255) # 주황 - 호명
COLOR_REACTION = (0, 255, 0)    # 연두 - 반응
COLOR_SUCCESS = (0, 255, 0)     # 초록 - 성공
COLOR_FAIL = (0, 0, 255)        # 빨강 - 실패
COLOR_CURRENT = (0, 0, 255)     # 빨강 - 현재 시점
COLOR_TEXT = (255, 255, 255)    # 흰색 - 텍스트
COLOR_BG = (0, 0, 0)            # 검정 - 배경
# 3D 좌표축 색상 (BGR)
COLOR_AXIS_X = (0, 0, 255)      # 빨강 - X축 (오른쪽)
COLOR_AXIS_Y = (0, 255, 0)      # 초록 - Y축 (아래쪽)
COLOR_AXIS_Z = (255, 0, 0)      # 파랑 - Z축 (정면/카메라 방향)

class VideoVisualizer:
    """
    비디오 시각화 도구
    
    PipelineContext를 입력받아 각 프레임에 분석 결과를 오버레이합니다.
    """
    
    def __init__(self, context: PipelineContext):
        """
        Args:
            context: 파이프라인 실행 결과
        """
        self.context = context
        self.frames = context.frames
        self.width = context.frame_width
        self.height = context.frame_height
        self.timestamps = context.frame_timestamps
        
    def draw_frame(self, frame_idx: int) -> np.ndarray:
        """
        프레임에 모든 시각화 요소 그리기
        
        Args:
            frame_idx: 프레임 인덱스
            
        Returns:
            시각화가 적용된 프레임
        """
        frame = self.frames[frame_idx].copy()
        ts = self.timestamps[frame_idx]
        
        # 1. 머리 영역
        frame = self.draw_head_boxes(frame, ts)
        
        # 2. 시선 벡터 & 각도 정보
        frame = self.draw_gaze_visualization(frame, ts)
        
        # 3. 오디오 타임라인
        frame = self.draw_audio_timeline(frame, ts)
        
        # 4. Trial 결과 패널
        frame = self.draw_trial_panel(frame, ts)
        
        # 5. 프레임 정보
        frame = self.draw_frame_info(frame, frame_idx, ts)
        
        return frame
    
    def draw_head_boxes(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """YOLO Head bounding box 그리기"""
        # 해당 시간의 탐지 결과
        detections = self.context.head_detections.get(timestamp, [])
        
        # 부모/아이 찾기
        parent_pos, child_det = None, None
        for ts, pos in self.context.parent_positions:
            if abs(ts - timestamp) < 0.001:
                parent_pos = pos
                break
        
        for ts, det in self.context.child_detections:
            if abs(ts - timestamp) < 0.001:
                child_det = det
                break
        
        # 부모 bbox (중심점으로 추정)
        if parent_pos is not None:
            x, y = int(parent_pos[0]), int(parent_pos[1])
            size = 50
            cv2.rectangle(frame, (x-size, y-size), (x+size, y+size), COLOR_PARENT, 2)
            cv2.putText(frame, "Parent", (x-size, y-size-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_PARENT, 2)
        
        # 아이 bbox
        if child_det is not None:
            bbox = child_det.bbox
            # BoundingBox는 (x, y, width, height) 정규화 좌표를 사용
            x1 = int(bbox.x * self.width)
            y1 = int(bbox.y * self.height)
            x2 = int((bbox.x + bbox.width) * self.width)
            y2 = int((bbox.y + bbox.height) * self.height)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_CHILD, 2)
            cv2.putText(frame, "Child", (x1, y1-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_CHILD, 2)
        
        return frame
    
    def draw_gaze_visualization(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """시선 벡터, 위치 벡터, 각도 정보 그리기 (3D 좌표축 포함)"""
        # Gaze 결과 찾기
        gaze_result = None
        for gr in self.context.gaze_frame_results:
            if abs(gr.timestamp - timestamp) < 0.001:
                gaze_result = gr
                break
        
        if gaze_result is None or not gaze_result.child_detected:
            return frame
        
        # Head Pose 찾기
        head_pose = None
        for ts, hp in self.context.head_pose_6d_results:
            if abs(ts - timestamp) < 0.001:
                head_pose = hp
                break
        
        # 아이 중심
        child_det = None
        for ts, det in self.context.child_detections:
            if abs(ts - timestamp) < 0.001:
                child_det = det
                break
        
        if child_det is None:
            return frame
        
        cx, cy = child_det.center_pixel(self.width, self.height)
        cx, cy = int(cx), int(cy)
        
        # 3D 좌표축 그리기 (아이 머리 중심에)
        frame = self._draw_3d_axes(frame, cx, cy, head_pose)
        
        # 시선 벡터 (노랑 화살표) - 3D 투영
        if gaze_result.gaze_vector is not None:
            gaze = gaze_result.gaze_vector
            frame = self._draw_3d_vector(frame, cx, cy, gaze, COLOR_GAZE, 3, "Gaze")
        
        # 위치 벡터 (하늘 화살표) - 3D 투영
        if gaze_result.position_vector is not None:
            pos = gaze_result.position_vector
            frame = self._draw_3d_vector(frame, cx, cy, pos, COLOR_POSITION, 2, "Pos")
        
        # 각도 정보 텍스트
        info_y = cy + 100
        if head_pose is not None:
            cv2.putText(frame, f"yaw: {head_pose.yaw:.1f}deg",
                       (cx - 60, info_y), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, COLOR_TEXT, 1)
            cv2.putText(frame, f"pitch: {head_pose.pitch:.1f}deg",
                       (cx - 60, info_y + 20), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, COLOR_TEXT, 1)
        
        # 시선 각도
        if gaze_result.angle_deg is not None:
            color = COLOR_SUCCESS if gaze_result.is_looking_at_parent else COLOR_FAIL
            status = "looking" if gaze_result.is_looking_at_parent else "not looking"
            cv2.putText(frame, f"angle: {gaze_result.angle_deg:.1f}deg [{status}]",
                       (cx - 60, info_y + 40), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, color, 2)
        
        return frame
    
    def _draw_3d_axes(self, frame: np.ndarray, cx: int, cy: int, 
                      head_pose=None, axis_len: int = 60) -> np.ndarray:
        """
        3D 좌표축 그리기
        
        좌표계:
        - X축 (빨강): 오른쪽이 양수
        - Y축 (초록): 아래쪽이 양수 (이미지 좌표계)
        - Z축 (파랑): 카메라/정면 방향이 양수 (화면 밖으로)
        """
        # 등각 투영 각도 (isometric-like)
        # Z축을 화면 왼쪽 위로 투영
        z_proj_x = -0.5  # Z축의 X 투영 비율
        z_proj_y = -0.5  # Z축의 Y 투영 비율 (위로)
        
        # X축 (빨강) - 오른쪽
        x_end = (cx + axis_len, cy)
        cv2.arrowedLine(frame, (cx, cy), x_end, COLOR_AXIS_X, 2, tipLength=0.2)
        cv2.putText(frame, "X", (x_end[0] + 5, x_end[1]), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_AXIS_X, 1)
        
        # Y축 (초록) - 아래쪽 (이미지 좌표계)
        y_end = (cx, cy + axis_len)
        cv2.arrowedLine(frame, (cx, cy), y_end, COLOR_AXIS_Y, 2, tipLength=0.2)
        cv2.putText(frame, "Y", (y_end[0] + 5, y_end[1]), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_AXIS_Y, 1)
        
        # Z축 (파랑) - 정면/카메라 방향 (화면 밖으로, 등각 투영)
        z_end_x = int(cx + axis_len * z_proj_x)
        z_end_y = int(cy + axis_len * z_proj_y)
        cv2.arrowedLine(frame, (cx, cy), (z_end_x, z_end_y), COLOR_AXIS_Z, 2, tipLength=0.2)
        cv2.putText(frame, "Z", (z_end_x - 15, z_end_y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_AXIS_Z, 1)
        
        return frame
    
    def _draw_3d_vector(self, frame: np.ndarray, cx: int, cy: int,
                        vector: np.ndarray, color: tuple, thickness: int,
                        label: str = "", arrow_len: int = 100) -> np.ndarray:
        """
        3D 벡터를 2D 화면에 투영하여 그리기
        
        Args:
            vector: [x, y, z] 3D 벡터 (정규화됨)
            color: BGR 색상
            thickness: 선 두께
            label: 레이블 (옵션)
            arrow_len: 화살표 길이 (픽셀)
        """
        if vector is None or len(vector) < 2:
            return frame
        
        # 등각 투영
        # X: 오른쪽이 양수
        # Y: 아래쪽이 양수 (이미지 좌표계)
        # Z: 왼쪽 위로 투영
        z_proj_x = -0.5
        z_proj_y = -0.5
        
        vx, vy = vector[0], vector[1]
        vz = vector[2] if len(vector) > 2 else 0.0
        
        # 2D 투영 계산
        proj_x = vx + vz * z_proj_x
        proj_y = vy + vz * z_proj_y
        
        end_x = int(cx + proj_x * arrow_len)
        end_y = int(cy + proj_y * arrow_len)  # 이미지 좌표계: Y는 아래가 양수
        
        cv2.arrowedLine(frame, (cx, cy), (end_x, end_y), color, thickness, tipLength=0.3)
        
        # 레이블 표시
        if label:
            cv2.putText(frame, label, (end_x + 5, end_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return frame
    
    def draw_audio_timeline(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """오디오 이벤트 타임라인 그리기"""
        timeline_height = 60
        timeline_y = self.height - timeline_height - 120
        timeline_width = self.width - 40
        timeline_x = 20
        
        cv2.rectangle(frame, (timeline_x, timeline_y),
                     (timeline_x + timeline_width, timeline_y + timeline_height),
                     COLOR_BG, -1)
        
        if not self.timestamps:
            return frame
        
        total_duration = self.timestamps[-1]
        
        def time_to_x(t: float) -> int:
            return timeline_x + int((t / total_duration) * timeline_width)
        
        # 호명 구간
        if self.context.name_call_events:
            for event in self.context.name_call_events:
                x1 = time_to_x(event.start_sec)
                x2 = time_to_x(event.end_sec)
                cv2.rectangle(frame, (x1, timeline_y + 5), (x2, timeline_y + 25),
                             COLOR_NAME_CALL, -1)
            cv2.putText(frame, "Name Call", (timeline_x, timeline_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_NAME_CALL, 1)
        
        # 음성 반응 구간
        if self.context.trial_results:
            for trial in self.context.trial_results:
                if trial.voice_detected and trial.voice_reaction:
                    x1 = time_to_x(trial.voice_reaction.start_sec)
                    x2 = time_to_x(trial.voice_reaction.end_sec)
                    cv2.rectangle(frame, (x1, timeline_y + 30), (x2, timeline_y + 50),
                                 COLOR_REACTION, -1)
            cv2.putText(frame, "Reaction", (timeline_x, timeline_y + 28),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_REACTION, 1)
        
        # 현재 시점
        current_x = time_to_x(timestamp)
        cv2.line(frame, (current_x, timeline_y), (current_x, timeline_y + timeline_height),
                COLOR_CURRENT, 2)
        
        return frame
    
    def draw_trial_panel(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """Trial 결과 패널 그리기"""
        if not self.context.trial_results:
            return frame
        
        panel_y = self.height - 100
        panel_x = 20
        
        cv2.rectangle(frame, (panel_x, panel_y), (self.width - 20, self.height - 20),
                     COLOR_BG, -1)
        
        cv2.putText(frame, "Trial Results:", (panel_x + 10, panel_y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)
        
        x_offset = panel_x + 150
        for i, trial in enumerate(self.context.trial_results):
            if trial.success:
                icon, color = "OK", COLOR_SUCCESS
            elif trial.voice_detected or trial.gaze_match:
                icon, color = "~", (0, 255, 255)
            else:
                icon, color = "X", COLOR_FAIL
            
            text = f"[{i+1}] {icon}"
            cv2.putText(frame, text, (x_offset, panel_y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            latency_text = f"{trial.latency_s:.2f}s" if trial.latency_s else "N/A"
            cv2.putText(frame, latency_text, (x_offset, panel_y + 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            x_offset += 100
        
        return frame
    
    def draw_frame_info(self, frame: np.ndarray, frame_idx: int, timestamp: float) -> np.ndarray:
        """프레임 정보 패널 그리기"""
        cv2.rectangle(frame, (0, 0), (300, 60), COLOR_BG, -1)
        
        fps = self.context.original_fps or 10.0
        cv2.putText(frame, f"Frame: {frame_idx+1}/{len(self.frames)}",
                   (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)
        cv2.putText(frame, f"Time: {timestamp:.2f}s",
                   (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)
        cv2.putText(frame, f"FPS: {fps:.1f}",
                   (200, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)
        
        return frame


def create_visualization_video(
    context: PipelineContext,
    output_path: str,
    fps: Optional[int] = None,
    codec: str = "mp4v",
    save_frames: bool = False
) -> str:
    """
    시각화 비디오 생성
    
    Args:
        context: 파이프라인 실행 결과
        output_path: 출력 비디오 경로
        fps: 출력 FPS (None이면 원본 FPS)
        codec: 비디오 코덱
        save_frames: 개별 프레임 이미지 저장 여부
        
    Returns:
        출력 비디오 경로
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 프레임 이미지 저장 폴더 생성
    if save_frames:
        frames_dir = output_path.parent / f"{output_path.stem}_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 프레임 이미지 저장 폴더: {frames_dir}")
    
    if fps is None:
        fps = int(context.original_fps) if context.original_fps else 10
    
    fourcc = cv2.VideoWriter_fourcc(*codec)
    out = cv2.VideoWriter(
        str(output_path), fourcc, fps,
        (context.frame_width, context.frame_height)
    )
    
    if not out.isOpened():
        raise RuntimeError(f"✖️ 비디오 Writer 열기 실패: {output_path}")
    
    logger.info(f"🎬 시각화 비디오 생성 시작: {output_path}")
    logger.info(f"   해상도: {context.frame_width}x{context.frame_height}, FPS: {fps}, 프레임 수: {len(context.frames)}")
    
    visualizer = VideoVisualizer(context)
    
    for i in range(len(context.frames)):
        vis_frame = visualizer.draw_frame(i)
        out.write(vis_frame)
        
        # 프레임 이미지 저장
        if save_frames:
            frame_path = frames_dir / f"frame_{i:04d}.jpg"
            cv2.imwrite(str(frame_path), vis_frame)
        
        if (i + 1) % 10 == 0:
            logger.info(f"   진행: {i+1}/{len(context.frames)} 프레임")
    
    out.release()
    logger.info(f"✅ 시각화 비디오 생성 완료: {output_path}")
    if save_frames:
        logger.info(f"✅ 프레임 이미지 저장 완료: {frames_dir}")
    
    return str(output_path)
