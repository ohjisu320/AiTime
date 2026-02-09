# services/name_non_facing/app/utils/visualize.py
"""
비디오 시각화 유틸리티

파이프라인 결과를 비디오에 오버레이하여 모니터링 및 디버깅을 지원합니다.

주요 기능:
    - YOLO Head bounding box 표시
    - Head Pose (yaw/pitch/roll) 시각화
    - 시선 원뿔 (Gaze Cone) + 블룸(Bloom) 이펙트
    - 오디오 이벤트 타임라인
    - Trial 결과 패널
    
Reference:
    - docs/1800_비디오_시각화_구현계획.md
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from app.models.head_pose_6d import HeadPose6D
from app.pipeline.context import PipelineContext

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

# ─────────────────────────────────────────────────────────────
# Gaze Cone 색상 프리셋 (BGR, alpha)
# 부모를 바라보는 정도에 따라 그라데이션
# ─────────────────────────────────────────────────────────────
CONE_COLOR_LOOKING = np.array([0, 255, 180], dtype=np.float64)      # 청록 (부모 응시)
CONE_COLOR_NOT_LOOKING = np.array([80, 60, 255], dtype=np.float64)  # 주홍 (비응시)
CONE_COLOR_MID = np.array([0, 220, 255], dtype=np.float64)          # 금색 (중간)

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
        from app.config import get_settings
        self._settings = get_settings()
        
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
        
        # Warmup 기간 체크 (tracking 안정화 대기)
        if frame_idx < self._settings.VISUALIZATION_WARMUP_FRAMES:
            # Warmup 안내 텍스트만 표시
            cv2.putText(
                frame,
                f"Tracking warmup... {frame_idx + 1}/{self._settings.VISUALIZATION_WARMUP_FRAMES}",
                (self.width // 2 - 150, self.height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2
            )
            return frame
        
        # 1. 머리 영역
        frame = self.draw_head_boxes(frame, ts)
        
        # 2. 시선 벡터 & 각도 정보
        frame = self.draw_gaze_visualization(frame, ts)
        
        # 3. 오디오 타임라인
        frame = self.draw_audio_timeline(frame, ts)
        
        # 4. Trial 결과 패널
        frame = self.draw_trial_panel(frame, ts)
        
        # 5. 좌측 지표 패널 (최종 결과 + 실시간 데이터)
        frame = self.draw_metrics_panel(frame, frame_idx, ts)
        
        return frame
    
    def draw_head_boxes(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """YOLO Head bounding box 그리기"""
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
        """시선 벡터, 위치 벡터, 각도 정보 + 시선 원뿔 그리기"""
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
        
        # ── 1. 시선 원뿔 + 블룸 (배경 레이어) ──
        if gaze_result.gaze_vector is not None:
            angle = (
                gaze_result.angle_deg
                if gaze_result.angle_deg is not None
                else 180.0
            )
            # 2D 투영: x,y만 사용
            gv = gaze_result.gaze_vector
            gaze_2d = np.array(
                [gv[0], gv[1]], dtype=np.float64,
            )
            g_norm = np.linalg.norm(gaze_2d)
            if g_norm > 1e-6:
                gaze_2d /= g_norm
            else:
                gaze_2d = np.array([0.0, 1.0])
            
            # DEBUG: Gaze 벡터 3D 정보 출력
            if head_pose:
                gaze_3d_text = f"Gaze3D: ({gv[0]:.2f}, {gv[1]:.2f}, {gv[2]:.2f})"
                cv2.putText(
                    frame, gaze_3d_text,
                    (cx - 60, cy - 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1,
                )
            
            frame = self._draw_gaze_cone_bloom(
                frame, cx, cy, gaze_2d,
                angle_deg=angle,
                is_looking=gaze_result.is_looking_at_parent,
            )
        
        # ── 2. 3D 좌표축 ──
        frame = self._draw_3d_axes(frame, cx, cy, head_pose)
        
        # ── 3. 시선 벡터 - 원뿔로 충분하므로 화살표 제거 ──
        # (Z축 등각 투영으로 인해 원뿔과 방향 불일치 발생하여 제거)
        
        # ── 3-1. 위치 벡터 (Parent-Child 중심점 연결선) ──
        if gaze_result.position_vector is not None:
            # 부모 위치 찾기
            parent_pos = None
            for ts, pos in self.context.parent_positions:
                if abs(ts - timestamp) < 0.001:
                    parent_pos = pos
                    break
            
            if parent_pos is not None:
                px, py = int(parent_pos[0]), int(parent_pos[1])
                # 위치 벡터 화살표 그리기 (하늘색)
                cv2.arrowedLine(
                    frame, (cx, cy), (px, py),
                    COLOR_POSITION, 2, tipLength=0.15
                )
                # 부모 중심점 표시
                cv2.circle(frame, (px, py), 5, COLOR_POSITION, -1)
        
        # ── 4. 각도 정보 텍스트 ──
        info_y = cy + 100
        if head_pose is not None:
            cv2.putText(
                frame, f"yaw: {head_pose.yaw:.1f}deg",
                (cx - 60, info_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1,
            )
            cv2.putText(
                frame, f"pitch: {head_pose.pitch:.1f}deg",
                (cx - 60, info_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1,
            )
        
        if gaze_result.angle_deg is not None:
            if gaze_result.is_looking_at_parent:
                color = COLOR_SUCCESS
                status = "looking"
            else:
                color = COLOR_FAIL
                status = "not looking"
            cv2.putText(
                frame,
                f"angle: {gaze_result.angle_deg:.1f}"
                f"deg [{status}]",
                (cx - 60, info_y + 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
            )
        
        return frame
    
    # ─────────────────────────────────────────────────────────
    # Gaze Cone + Bloom 렌더링
    # ─────────────────────────────────────────────────────────
    
    def _angle_to_cone_color(self, angle_deg: float) -> np.ndarray:
        """
        시선 각도 → 원뿔 색상 (BGR float)
        
        0°  = CONE_COLOR_LOOKING   (청록)
        45° = CONE_COLOR_MID       (금색)  
        90°+ = CONE_COLOR_NOT_LOOKING (주홍)
        """
        t = np.clip(angle_deg / 90.0, 0.0, 1.0)
        if t < 0.5:
            # 청록 → 금색
            ratio = t * 2.0
            color = CONE_COLOR_LOOKING * (1 - ratio) + CONE_COLOR_MID * ratio
        else:
            # 금색 → 주홍
            ratio = (t - 0.5) * 2.0
            color = CONE_COLOR_MID * (1 - ratio) + CONE_COLOR_NOT_LOOKING * ratio
        return color
    
    def _project_3d_to_2d(self, vx: float, vy: float, vz: float) -> Tuple[float, float]:
        """3D 벡터를 2D 화면으로 등각 투영"""
        z_proj_x, z_proj_y = -0.5, -0.5
        px = vx + vz * z_proj_x
        py = vy + vz * z_proj_y
        return px, py

    def _draw_gaze_cone_bloom(
        self, frame: np.ndarray,
        cx: int, cy: int,
        gaze_vector: np.ndarray,
        angle_deg: float = 90.0,
        is_looking: bool = False,
        cone_length: int = 160,
        cone_half_angle: float = 14.0,
        num_slices: int = 20,
        bloom_sigma: int = 21,
    ) -> np.ndarray:
        """
        볼류메트릭 시선 원뿔 + 블룸 이펙트 렌더링 (최적화)
        
        ROI 기반 렌더링으로 고속 처리:
            1. 원뿔 바운딩 박스만큼의 ROI만 할당
            2. 단일 glow 레이어에 모든 타원 직접 누적
            3. ROI 영역만 가우시안 블러 + 합성
        
        Args:
            frame: 입력 BGR 프레임
            cx, cy: 원뿔 시작점 (아이 머리 중심)
            gaze_vector: [x, y, z] 정규화된 시선 벡터
            angle_deg: 부모와의 각도 (색상 결정)
            is_looking: 부모 응시 여부 (블룸 강도)
            cone_length: 원뿔 길이 (px)
            cone_half_angle: 원뿔 반각 (도)
            num_slices: 원뿔 단면 수
            bloom_sigma: 블룸 블러 시그마
        """
        h, w = frame.shape[:2]
        
        # ── 1. 시선 방향 (2D 투영 완료된 벡터 수신) ──
        dir_x = float(gaze_vector[0])
        dir_y = float(gaze_vector[1])
        
        dir_mag = math.sqrt(dir_x * dir_x + dir_y * dir_y)
        if dir_mag < 1e-6:
            return frame
        dir_x /= dir_mag
        dir_y /= dir_mag
        
        # ── 2. ROI 바운딩 박스 계산 ──
        max_r = cone_length * math.tan(
            math.radians(cone_half_angle)
        )
        margin = int(bloom_sigma * 2.5)
        
        # 원뿔 끝점
        end_x = cx + dir_x * cone_length
        end_y = cy + dir_y * cone_length
        
        roi_x1 = int(min(cx, end_x) - max_r - margin)
        roi_y1 = int(min(cy, end_y) - max_r - margin)
        roi_x2 = int(max(cx, end_x) + max_r + margin)
        roi_y2 = int(max(cy, end_y) + max_r + margin)
        
        # 프레임 경계 클리핑
        roi_x1 = max(0, roi_x1)
        roi_y1 = max(0, roi_y1)
        roi_x2 = min(w, roi_x2)
        roi_y2 = min(h, roi_y2)
        
        roi_w = roi_x2 - roi_x1
        roi_h = roi_y2 - roi_y1
        if roi_w < 10 or roi_h < 10:
            return frame
        
        # ROI 내 원점 오프셋
        ox = cx - roi_x1
        oy = cy - roi_y1
        
        # ── 3. 원뿔 색상 ──
        base_color = self._angle_to_cone_color(angle_deg)
        
        # ── 4. ROI 크기 glow 레이어 (float32) ──
        glow = np.zeros((roi_h, roi_w, 3), dtype=np.float32)
        
        # ── 5. 원뿔 단면 (뒤→앞 순서) ──
        ell_angle = math.degrees(math.atan2(dir_y, dir_x))
        
        for i in range(num_slices, 0, -1):
            t = i / num_slices
            
            dist = cone_length * t
            sx = int(ox + dir_x * dist)
            sy = int(oy + dir_y * dist)
            
            # 반지름 (선형)
            radius = int(max_r * t)
            if radius < 1:
                continue
            
            # 밝기 감쇠
            alpha = 0.45 * (1.0 - t * 0.65)
            
            # 중심부 흰색 블렌드
            wb = max(0.0, 1.0 - t * 1.5)
            sc = base_color * (1 - wb) + 255.0 * wb
            
            a_maj = radius
            a_min = radius
            
            # 외곽 글로우 (큰 타원, 낮은 밝기)
            outer = int(a_maj * 1.4)
            cv2.ellipse(
                glow, (sx, sy), (outer, outer),
                ell_angle, 0, 360,
                (sc * alpha * 0.3).tolist(), -1, cv2.LINE_AA,
            )
            # 메인 타원
            cv2.ellipse(
                glow, (sx, sy), (a_maj, a_min),
                ell_angle, 0, 360,
                (sc * alpha).tolist(), -1, cv2.LINE_AA,
            )
        
        # ── 6. 코어 라인 (밝은 중심선) ──
        core_ex = int(ox + dir_x * cone_length * 0.85)
        core_ey = int(oy + dir_y * cone_length * 0.85)
        cc = (base_color * 0.3 + 255.0 * 0.7).tolist()
        cv2.line(glow, (ox, oy), (core_ex, core_ey),
                 cc, 2, cv2.LINE_AA)
        
        # ── 7. 시작점 글로우 ──
        cv2.circle(glow, (ox, oy), 6,
                   (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(glow, (ox, oy), 12,
                   (base_color * 0.7).tolist(), -1, cv2.LINE_AA)
        
        # ── 8. 블룸 (ROI만 블러) ──
        ks = bloom_sigma * 2 + 1
        bloomed = cv2.GaussianBlur(glow, (ks, ks), bloom_sigma)
        
        combined = glow * 0.7 + bloomed * 0.8
        
        if is_looking:
            ks2 = bloom_sigma * 3
            ks2 = ks2 + 1 if ks2 % 2 == 0 else ks2
            extra = cv2.GaussianBlur(
                glow, (ks2, ks2), bloom_sigma * 1.5,
            )
            combined += extra * 0.25
        
        # ── 9. Additive Blend (ROI만) ──
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        result = roi.astype(np.float32) + combined
        np.clip(result, 0, 255, out=result)
        frame[roi_y1:roi_y2, roi_x1:roi_x2] = result.astype(
            np.uint8
        )
        
        return frame
    
    def _draw_position_guide(
        self, frame: np.ndarray,
        cx: int, cy: int,
        position_vector: np.ndarray,
        length: int = 120,
    ) -> np.ndarray:
        """부모 방향 가이드 (점선 + 작은 다이아몬드)"""
        if position_vector is None or len(position_vector) < 2:
            return frame
        
        vx, vy = position_vector[0], position_vector[1]
        vz = position_vector[2] if len(position_vector) > 2 else 0.0
        dx, dy = self._project_3d_to_2d(vx, vy, vz)
        
        mag = math.sqrt(dx * dx + dy * dy)
        if mag < 1e-6:
            return frame
        dx /= mag
        dy /= mag
        
        # 점선 그리기
        num_dashes = 12
        dash_len = length / (num_dashes * 2)
        for i in range(num_dashes):
            t0 = (2 * i) * dash_len
            t1 = (2 * i + 1) * dash_len
            p0 = (int(cx + dx * t0), int(cy + dy * t0))
            p1 = (int(cx + dx * t1), int(cy + dy * t1))
            # 반투명 효과를 위해 밝기 감소
            alpha = max(0.2, 1.0 - (t0 / length) * 0.6)
            color = tuple(int(c * alpha) for c in COLOR_POSITION)
            cv2.line(frame, p0, p1, color, 1, cv2.LINE_AA)
        
        # 끝점 다이아몬드
        end_x = int(cx + dx * length)
        end_y = int(cy + dy * length)
        d = 5
        pts = np.array([
            [end_x, end_y - d],
            [end_x + d, end_y],
            [end_x, end_y + d],
            [end_x - d, end_y],
        ], dtype=np.int32)
        cv2.fillPoly(frame, [pts], COLOR_POSITION, cv2.LINE_AA)
        
        cv2.putText(frame, "Parent", (end_x + 8, end_y + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, COLOR_POSITION, 1, cv2.LINE_AA)
        
        return frame
    
    def _draw_gaze_hud(
        self, frame: np.ndarray,
        cx: int, cy: int,
        head_pose: Optional[HeadPose6D],
        gaze_result,
    ) -> np.ndarray:
        """시선 정보 HUD (Head-Up Display) — 머리 아래에 표시"""
        info_y = cy + 80
        
        # 반투명 배경 박스
        box_x = cx - 85
        box_w = 170
        box_h = 64 if head_pose is not None else 28
        overlay = frame.copy()
        cv2.rectangle(overlay, (box_x, info_y - 4), (box_x + box_w, info_y + box_h),
                      (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Head Pose 값
        if head_pose is not None:
            cv2.putText(frame, f"Y:{head_pose.yaw:+.0f}",
                        (box_x + 6, info_y + 14), cv2.FONT_HERSHEY_SIMPLEX,
                        0.42, (180, 180, 180), 1, cv2.LINE_AA)
            cv2.putText(frame, f"P:{head_pose.pitch:+.0f}",
                        (box_x + 62, info_y + 14), cv2.FONT_HERSHEY_SIMPLEX,
                        0.42, (180, 180, 180), 1, cv2.LINE_AA)
            cv2.putText(frame, f"R:{head_pose.roll:+.0f}",
                        (box_x + 118, info_y + 14), cv2.FONT_HERSHEY_SIMPLEX,
                        0.42, (180, 180, 180), 1, cv2.LINE_AA)
        
        # 시선 각도 + 상태
        if gaze_result.angle_deg is not None:
            angle = gaze_result.angle_deg
            if gaze_result.is_looking_at_parent:
                status_text = "LOOKING"
                status_color = (0, 255, 180)  # 청록
                angle_color = (0, 255, 180)
            else:
                status_text = "NOT LOOKING"
                status_color = (80, 80, 255)  # 연빨강
                angle_color = (80, 140, 255)  # 주황
            
            y_line = info_y + (38 if head_pose is not None else 18)
            cv2.putText(frame, f"{angle:.1f}deg",
                        (box_x + 6, y_line), cv2.FONT_HERSHEY_SIMPLEX,
                        0.48, angle_color, 1, cv2.LINE_AA)
            cv2.putText(frame, status_text,
                        (box_x + 80, y_line), cv2.FONT_HERSHEY_SIMPLEX,
                        0.42, status_color, 1, cv2.LINE_AA)
            
            # 상태 인디케이터 도트
            dot_x = box_x + box_w - 12
            dot_y = y_line - 5
            cv2.circle(frame, (dot_x, dot_y), 5, status_color, -1, cv2.LINE_AA)
        
        return frame
    
    def _draw_3d_axes(self, frame: np.ndarray, cx: int, cy: int, 
                      head_pose=None, axis_len: int = 30) -> np.ndarray:
        """
        3D 좌표축 그리기 (소형, 보조 표시)
        
        좌표계:
        - X축 (빨강): 오른쪽이 양수
        - Y축 (초록): 아래쪽이 양수 (이미지 좌표계)
        - Z축 (파랑): 카메라/정면 방향이 양수 (화면 밖으로)
        """
        # 원뿔 시각화의 보조이므로 좌측 상단 오프셋에 작게
        ox = cx - 60
        oy = cy - 50
        
        z_proj_x, z_proj_y = -0.5, -0.5
        
        tip = 0.25
        aa = cv2.LINE_AA
        
        # X축
        x_end = (ox + axis_len, oy)
        cv2.arrowedLine(
            frame, (ox, oy), x_end,
            COLOR_AXIS_X, 1, tipLength=tip, line_type=aa,
        )
        cv2.putText(
            frame, "x", (x_end[0] + 2, x_end[1] + 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.3, COLOR_AXIS_X, 1, aa,
        )
        
        # Y축
        y_end = (ox, oy + axis_len)
        cv2.arrowedLine(
            frame, (ox, oy), y_end,
            COLOR_AXIS_Y, 1, tipLength=tip, line_type=aa,
        )
        cv2.putText(
            frame, "y", (y_end[0] + 3, y_end[1] + 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.3, COLOR_AXIS_Y, 1, aa,
        )
        
        # Z축
        zx = int(ox + axis_len * z_proj_x)
        zy = int(oy + axis_len * z_proj_y)
        z_end = (zx, zy)
        cv2.arrowedLine(
            frame, (ox, oy), z_end,
            COLOR_AXIS_Z, 1, tipLength=tip, line_type=aa,
        )
        cv2.putText(
            frame, "z", (z_end[0] - 10, z_end[1]),
            cv2.FONT_HERSHEY_SIMPLEX, 0.3, COLOR_AXIS_Z, 1, aa,
        )
        
        return frame
    
    def _draw_3d_vector(self, frame: np.ndarray, cx: int, cy: int,
                        vector: np.ndarray, color: tuple, thickness: int,
                        label: str = "", arrow_len: int = 100) -> np.ndarray:
        """3D 벡터를 2D 화면에 등각 투영하여 화살표로 그리기"""
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
                if trial.voice_detected and trial.voice_start_s is not None:
                    x1 = time_to_x(trial.voice_start_s)
                    x2 = time_to_x(trial.voice_end_s or trial.voice_start_s + 0.5)
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
    
    # ─────────────────────────────────────────────────────────
    # 좌측 지표 오버레이 패널
    # ─────────────────────────────────────────────────────────

    # 패널 레이아웃 상수
    _PNL_X = 8           # 좌측 여백
    _PNL_W = 310         # 패널 폭
    _PNL_PAD = 10        # 내부 패딩
    _PNL_BG_ALPHA = 0.60 # 배경 투명도
    _FONT = cv2.FONT_HERSHEY_SIMPLEX
    _AA = cv2.LINE_AA

    def draw_metrics_panel(
        self, frame: np.ndarray,
        frame_idx: int, timestamp: float,
    ) -> np.ndarray:
        """
        화면 좌측 통합 지표 패널

        ┌──────────────────────────┐
        │ ▶ Frame / Time / FPS     │  ← _section_frame_info
        │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
        │ 📊 Pipeline Summary      │  ← _section_pipeline
        │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
        │ 👁 Gaze (실시간)         │  ← _section_gaze_realtime
        │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
        │ 🎯 Trial Results         │  ← _section_trials
        │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
        │ 📋 ADOS Score            │  ← _section_ados
        └──────────────────────────┘
        """
        x = self._PNL_X
        w = self._PNL_W
        pad = self._PNL_PAD

        # 각 섹션을 임시 프레임 위에 그려서 높이 계산
        sections: list = []
        y_cursor = pad

        y_cursor = self._section_frame_info(
            frame, x, w, y_cursor, pad, frame_idx, timestamp,
        )
        y_cursor = self._draw_separator(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._section_pipeline(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._draw_separator(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._section_gaze_realtime(
            frame, x, w, y_cursor, pad, timestamp,
        )
        y_cursor = self._draw_separator(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._section_trials(
            frame, x, w, y_cursor, pad, timestamp,
        )
        y_cursor = self._draw_separator(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._section_ados(
            frame, x, w, y_cursor, pad,
        )
        y_cursor += pad

        # 반투명 배경 (모든 텍스트 뒤에 한 번에)
        panel_h = min(y_cursor, self.height - 4)
        overlay = frame.copy()
        cv2.rectangle(
            overlay, (x, 0), (x + w, panel_h),
            COLOR_BG, -1,
        )
        cv2.addWeighted(
            overlay, self._PNL_BG_ALPHA,
            frame, 1.0 - self._PNL_BG_ALPHA, 0, frame,
        )

        # 텍스트를 다시 그림 (배경 위에)
        y_cursor = pad
        y_cursor = self._section_frame_info(
            frame, x, w, y_cursor, pad, frame_idx, timestamp,
        )
        y_cursor = self._draw_separator(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._section_pipeline(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._draw_separator(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._section_gaze_realtime(
            frame, x, w, y_cursor, pad, timestamp,
        )
        y_cursor = self._draw_separator(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._section_trials(
            frame, x, w, y_cursor, pad, timestamp,
        )
        y_cursor = self._draw_separator(
            frame, x, w, y_cursor, pad,
        )
        y_cursor = self._section_ados(
            frame, x, w, y_cursor, pad,
        )

        # 패널 테두리
        cv2.rectangle(
            frame, (x, 0), (x + w, panel_h),
            (80, 80, 80), 1,
        )

        return frame

    # ── 헬퍼: 구분선 ──
    def _draw_separator(
        self, frame, x, w, y, pad,
    ) -> int:
        sy = y + 4
        cv2.line(
            frame, (x + pad, sy), (x + w - pad, sy),
            (80, 80, 80), 1, self._AA,
        )
        return sy + 6

    # ── 헬퍼: 라벨+값 한 줄 ──
    def _put_kv(
        self, frame, x, y, label, value,
        lcolor=(160, 160, 160), vcolor=COLOR_TEXT,
        lscale=0.38, vscale=0.42,
    ) -> int:
        cv2.putText(
            frame, label, (x, y),
            self._FONT, lscale, lcolor, 1, self._AA,
        )
        cv2.putText(
            frame, str(value), (x + 100, y),
            self._FONT, vscale, vcolor, 1, self._AA,
        )
        return y + 18

    # ── 섹션 1: 프레임 정보 ──
    def _section_frame_info(
        self, frame, x, w, y, pad,
        frame_idx, timestamp,
    ) -> int:
        lx = x + pad
        total = len(self.frames)
        fps = self.context.original_fps or 10.0
        dur = self.timestamps[-1] if self.timestamps else 0

        cv2.putText(
            frame, "FRAME INFO",
            (lx, y + 12), self._FONT, 0.40,
            (200, 200, 200), 1, self._AA,
        )
        y += 22

        y = self._put_kv(
            frame, lx, y, "Frame",
            f"{frame_idx + 1} / {total}",
        )
        y = self._put_kv(
            frame, lx, y, "Time",
            f"{timestamp:.2f}s / {dur:.1f}s",
        )
        y = self._put_kv(
            frame, lx, y, "Orig FPS",
            f"{fps:.1f}",
        )
        y = self._put_kv(
            frame, lx, y, "Resolution",
            f"{self.width}x{self.height}",
        )
        return y

    # ── 섹션 2: 파이프라인 요약 ──
    def _section_pipeline(
        self, frame, x, w, y, pad,
    ) -> int:
        lx = x + pad
        ctx = self.context

        cv2.putText(
            frame, "PIPELINE",
            (lx, y + 12), self._FONT, 0.40,
            (200, 200, 200), 1, self._AA,
        )
        y += 22

        status_str = ctx.status.value.upper()
        sc = COLOR_SUCCESS if status_str == "COMPLETED" else (
            COLOR_FAIL if status_str == "FAILED" else (0, 200, 255)
        )
        y = self._put_kv(
            frame, lx, y, "Status", status_str, vcolor=sc,
        )

        # Stage별 소요시간 (있으면)
        for stage, elapsed in ctx.processing_times.items():
            short = stage.replace("Stage", "")
            y = self._put_kv(
                frame, lx, y, f"  {short}",
                f"{elapsed:.2f}s",
                lcolor=(130, 130, 130),
                vcolor=(180, 180, 180),
            )

        total = sum(ctx.processing_times.values())
        if total > 0:
            y = self._put_kv(
                frame, lx, y, "  Total",
                f"{total:.2f}s",
                vcolor=(220, 220, 220),
            )

        # 탐지 통계
        n_child = sum(
            1 for g in ctx.gaze_frame_results
            if g.child_detected
        )
        n_total = len(ctx.gaze_frame_results) or len(
            ctx.frames or []
        )
        pct = (
            n_child / n_total * 100 if n_total else 0
        )
        y = self._put_kv(
            frame, lx, y, "Child Det.",
            f"{n_child}/{n_total} ({pct:.0f}%)",
        )

        n_look = sum(
            1 for g in ctx.gaze_frame_results
            if g.is_looking_at_parent
        )
        y = self._put_kv(
            frame, lx, y, "Looking",
            f"{n_look}/{n_total}",
            vcolor=COLOR_SUCCESS if n_look > 0 else (
                180, 180, 180
            ),
        )

        mode = "1st-person" if ctx.is_first_person_view else (
            "2-person"
        )
        y = self._put_kv(
            frame, lx, y, "Mode", mode,
        )

        return y

    # ── 섹션 3: 실시간 시선 데이터 ──
    def _section_gaze_realtime(
        self, frame, x, w, y, pad, timestamp,
    ) -> int:
        lx = x + pad
        ctx = self.context

        cv2.putText(
            frame, "GAZE (realtime)",
            (lx, y + 12), self._FONT, 0.40,
            (200, 200, 200), 1, self._AA,
        )
        y += 22

        # 현재 프레임 gaze
        gaze_result = None
        for gr in ctx.gaze_frame_results:
            if abs(gr.timestamp - timestamp) < 0.001:
                gaze_result = gr
                break

        if gaze_result is None or not gaze_result.child_detected:
            y = self._put_kv(
                frame, lx, y, "Child", "NOT DETECTED",
                vcolor=(100, 100, 100),
            )
            return y

        # 시선 각도 + 상태
        angle = gaze_result.angle_deg
        looking = gaze_result.is_looking_at_parent
        sc = COLOR_SUCCESS if looking else COLOR_FAIL
        tag = "LOOKING" if looking else "NOT LOOKING"

        y = self._put_kv(
            frame, lx, y, "Angle",
            f"{angle:.1f} deg", vcolor=sc,
        )
        y = self._put_kv(
            frame, lx, y, "Status", tag, vcolor=sc,
        )

        # 시선 게이지 바
        bar_x = lx
        bar_w = w - pad * 2
        bar_h = 10
        bar_y = y
        # 배경
        cv2.rectangle(
            frame,
            (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h),
            (40, 40, 40), -1,
        )
        # 채움 (0°=꽉참, 180°=빔)
        fill = max(0.0, 1.0 - angle / 180.0)
        fill_w = int(bar_w * fill)
        if fill_w > 0:
            cv2.rectangle(
                frame,
                (bar_x, bar_y),
                (bar_x + fill_w, bar_y + bar_h),
                sc, -1,
            )
        # 임계선
        from app.config import get_settings
        settings = get_settings()
        thr = settings.GAZE_ANGLE_THRESHOLD_DEG
        thr_x = bar_x + int(
            bar_w * (1.0 - thr / 180.0)
        )
        cv2.line(
            frame,
            (thr_x, bar_y - 2),
            (thr_x, bar_y + bar_h + 2),
            (0, 255, 255), 1, self._AA,
        )
        cv2.putText(
            frame, f"{thr:.0f}",
            (thr_x + 2, bar_y + bar_h + 10),
            self._FONT, 0.28, (0, 255, 255), 1, self._AA,
        )
        y = bar_y + bar_h + 16

        # Head Pose
        head_pose = None
        for ts, hp in ctx.head_pose_6d_results:
            if abs(ts - timestamp) < 0.001:
                head_pose = hp
                break
        if head_pose is not None:
            y = self._put_kv(
                frame, lx, y, "Yaw",
                f"{head_pose.yaw:+.1f} deg",
            )
            y = self._put_kv(
                frame, lx, y, "Pitch",
                f"{head_pose.pitch:+.1f} deg",
            )
            y = self._put_kv(
                frame, lx, y, "Roll",
                f"{head_pose.roll:+.1f} deg",
            )

        # 시선/위치 벡터
        gv = gaze_result.gaze_vector
        pv = gaze_result.position_vector
        if gv is not None:
            gvs = ", ".join(f"{v:+.2f}" for v in gv)
            y = self._put_kv(
                frame, lx, y, "Gaze V.",
                f"[{gvs}]",
                vcolor=COLOR_GAZE, vscale=0.34,
            )
        if pv is not None:
            pvs = ", ".join(f"{v:+.2f}" for v in pv)
            y = self._put_kv(
                frame, lx, y, "Pos V.",
                f"[{pvs}]",
                vcolor=COLOR_POSITION, vscale=0.34,
            )

        return y

    # ── 섹션 4: Trial 결과 ──
    def _section_trials(
        self, frame, x, w, y, pad, timestamp,
    ) -> int:
        lx = x + pad
        ctx = self.context
        trials = ctx.trial_results

        cv2.putText(
            frame, "TRIALS",
            (lx, y + 12), self._FONT, 0.40,
            (200, 200, 200), 1, self._AA,
        )
        y += 22

        if not trials:
            y = self._put_kv(
                frame, lx, y, "Trials", "NONE",
                vcolor=(100, 100, 100),
            )
            return y

        n_ok = sum(1 for t in trials if t.success)
        y = self._put_kv(
            frame, lx, y, "Total",
            f"{n_ok}/{len(trials)} passed",
            vcolor=COLOR_SUCCESS if n_ok > 0 else COLOR_FAIL,
        )

        for i, tr in enumerate(trials):
            sc = COLOR_SUCCESS if tr.success else COLOR_FAIL
            icon = "OK" if tr.success else "FAIL"
            lat = (
                f"{tr.latency_s:.2f}s" if tr.latency_s else "N/A"
            )
            voice = "V" if tr.voice_detected else "-"
            gaze = "G" if tr.gaze_match else "-"

            line = f"#{i+1} {icon}  lat={lat}  [{voice}|{gaze}]"
            cv2.putText(
                frame, line, (lx + 4, y + 2),
                self._FONT, 0.36, sc, 1, self._AA,
            )
            y += 16

            # 활성 trial 하이라이트
            if (
                tr.trigger_start_s is not None
                and tr.trigger_end_s is not None
            ):
                t_end = tr.trigger_end_s + (
                    tr.latency_s or 5.0
                )
                if tr.trigger_start_s <= timestamp <= t_end:
                    cv2.rectangle(
                        frame,
                        (lx, y - 14),
                        (lx + w - pad * 2, y + 2),
                        sc, 1,
                    )

        return y

    # ── 섹션 5: ADOS 점수 ──
    def _section_ados(
        self, frame, x, w, y, pad,
    ) -> int:
        lx = x + pad
        ctx = self.context

        cv2.putText(
            frame, "ADOS SCORE",
            (lx, y + 12), self._FONT, 0.40,
            (200, 200, 200), 1, self._AA,
        )
        y += 22

        # B7 점수 (0~3, 낮을수록 좋음)
        b7 = ctx.ados_b7
        if b7 is not None:
            b7_color = (
                COLOR_SUCCESS if b7 == 0 else
                (0, 255, 255) if b7 == 1 else
                (0, 165, 255) if b7 == 2 else
                COLOR_FAIL
            )
            y = self._put_kv(
                frame, lx, y, "B7",
                f"{b7} / 3",
                vcolor=b7_color,
            )
            # B7 바
            bar_x = lx + 100
            bar_w2 = w - pad * 2 - 100
            for seg in range(4):
                sx = bar_x + int(bar_w2 * seg / 4)
                sw = int(bar_w2 / 4) - 2
                c = (
                    COLOR_SUCCESS if seg == 0 else
                    (0, 255, 255) if seg == 1 else
                    (0, 165, 255) if seg == 2 else
                    COLOR_FAIL
                )
                fill = -1 if seg <= b7 else 1
                cv2.rectangle(
                    frame,
                    (sx, y - 2), (sx + sw, y + 8),
                    c, fill,
                )
            y += 16
        else:
            y = self._put_kv(
                frame, lx, y, "B7", "N/A",
                vcolor=(100, 100, 100),
            )

        # B18
        b18 = ctx.ados_b18
        if b18 is not None:
            b18c = COLOR_SUCCESS if b18 else COLOR_FAIL
            tag = "YES" if b18 else "NO"
            y = self._put_kv(
                frame, lx, y, "B18", tag, vcolor=b18c,
            )
        else:
            y = self._put_kv(
                frame, lx, y, "B18", "N/A",
                vcolor=(100, 100, 100),
            )

        # 에러/경고 요약
        if ctx.errors:
            y = self._put_kv(
                frame, lx, y, "Errors",
                f"{len(ctx.errors)}",
                vcolor=COLOR_FAIL,
            )
        if ctx.warnings:
            y = self._put_kv(
                frame, lx, y, "Warns",
                f"{len(ctx.warnings)}",
                vcolor=(0, 200, 255),
            )

        return y

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
