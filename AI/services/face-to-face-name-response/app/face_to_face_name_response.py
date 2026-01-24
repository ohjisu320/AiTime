import logging
import os
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
import numpy.typing as npt

from app.rtn.audio.segments import merge_close_segments
from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    FaceDetConfig,
    GazeSmoothConfig,
    ROIConfig,
    RoleAssignConfig,
    TrackConfig,
    VADConfig,
)
from app.rtn.tracking.sort_tracker import SortTracker
from app.rtn.types import BBox, FrameBGR, Landmarks, MaskU8, Track
from app.rtn.vision.indices import (
    LEFT_EYE_CONTOUR,
    LEFT_EYE_OUTER,
    LEFT_IRIS,
    RIGHT_EYE_CONTOUR,
    RIGHT_EYE_OUTER,
    RIGHT_IRIS,
)
from app.rtn.vision.mp_face_detector import FaceDetectorMP, FaceMeshMP

# -----------------------------
# Logging
# -----------------------------
logger = logging.getLogger("RTNAnalyzer")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


# -----------------------------
# Utils
# -----------------------------
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def iou_xyxy(a: BBox, b: BBox) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    iw = max(0.0, x2 - x1)
    ih = max(0.0, y2 - y1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, (a[2] - a[0])) * max(0.0, (a[3] - a[1]))
    area_b = max(0.0, (b[2] - b[0])) * max(0.0, (b[3] - b[1]))
    union = area_a + area_b - inter + 1e-9
    return float(inter / union)


def bbox_area_xyxy(b: BBox) -> float:
    return max(0.0, (b[2] - b[0])) * max(0.0, (b[3] - b[1]))


def smooth_xy(
    prev_xy: tuple[float, float] | None,
    cur_xy: tuple[float, float],
    alpha: float = 0.25,
    max_jump: float = 0.12,
) -> tuple[float, float]:
    cx, cy = cur_xy
    if prev_xy is None:
        return (float(cx), float(cy))
    px, py = prev_xy
    cx = px + float(np.clip(cx - px, -max_jump, +max_jump))
    cy = py + float(np.clip(cy - py, -max_jump, +max_jump))
    sx = alpha * cx + (1 - alpha) * px
    sy = alpha * cy + (1 - alpha) * py
    return (float(sx), float(sy))


def contact_by_raycast(
    eye_mask: MaskU8,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    n_samples: int = 11,
) -> bool:
    h, w = eye_mask.shape[:2]
    sx, sy = start_xy
    ex, ey = end_xy
    for i in range(n_samples):
        t = i / (n_samples - 1)
        x = int(clamp(sx + (ex - sx) * t, 0, w - 1))
        y = int(clamp(sy + (ey - sy) * t, 0, h - 1))
        if eye_mask[y, x] > 0:
            return True
    return False


def crop_face_square(
    frame_bgr: FrameBGR,
    bbox_xyxy: BBox,
    margin: float = 0.35,
) -> tuple[FrameBGR, tuple[int, int]]:
    h, w = frame_bgr.shape[:2]
    x1, y1, x2, y2 = bbox_xyxy
    bw = x2 - x1
    bh = y2 - y1

    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0

    side = max(bw, bh) * (1.0 + 2.0 * margin)
    side = max(2.0, side)

    cx1 = int(clamp(cx - side / 2.0, 0, w - 1))
    cy1 = int(clamp(cy - side / 2.0, 0, h - 1))
    cx2 = int(clamp(cx + side / 2.0, 0, w - 1))
    cy2 = int(clamp(cy + side / 2.0, 0, h - 1))

    crop = frame_bgr[cy1:cy2, cx1:cx2].copy()
    return crop, (cx1, cy1)


# -----------------------------
# Audio extraction / VAD
# -----------------------------


class SileroVAD:
    """
    torch.hub 기반 Silero VAD 래퍼.
    - 최초 1회 모델 다운로드 필요할 수 있음
    """

    _loaded: bool = False
    _model: Any | None = None
    _get_speech_timestamps: Callable[..., Any] | None = None

    def __init__(self, cfg: VADConfig) -> None:
        self.cfg = cfg
        self._ensure_loaded()

    @classmethod
    def _ensure_loaded(cls) -> None:
        if cls._loaded:
            return

        import torch  # noqa: PLC0415

        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        (
            get_speech_timestamps,
            _save_audio,
            _read_audio,
            _VADIterator,
            _collect_chunks,
        ) = utils

        cls._model = model
        cls._get_speech_timestamps = staticmethod(get_speech_timestamps)
        cls._loaded = True


# -----------------------------
# Gaze / ROI
# -----------------------------
def iris_center(pts: Landmarks, iris_indices: Sequence[int]) -> tuple[float, float]:
    xs = [pts[i][0] for i in iris_indices]
    ys = [pts[i][1] for i in iris_indices]
    return float(np.mean(xs)), float(np.mean(ys))


def eye_ratio(pts: Landmarks) -> tuple[float, float]:
    def one_eye(
        iris_idx: Sequence[int],
        contour_idx: Sequence[int],
    ) -> tuple[float, float, float]:
        cx, cy = iris_center(pts, iris_idx)
        eye = np.array(
            [[pts[i][0], pts[i][1]] for i in contour_idx],
            dtype=np.float32,
        )
        x0, x1 = float(eye[:, 0].min()), float(eye[:, 0].max())
        y0, y1 = float(eye[:, 1].min()), float(eye[:, 1].max())
        xr = (cx - x0) / ((x1 - x0) + 1e-6)
        yr = (cy - y0) / ((y1 - y0) + 1e-6)
        q = (x1 - x0) * (y1 - y0)
        return float(xr), float(yr), float(q)

    lxr, lyr, lq = one_eye(LEFT_IRIS, LEFT_EYE_CONTOUR)
    rxr, ryr, rq = one_eye(RIGHT_IRIS, RIGHT_EYE_CONTOUR)

    qsum = lq + rq
    if qsum > 1e-6:
        wl = lq / qsum
        wr = rq / qsum
        xr = wl * lxr + wr * rxr
        yr = wl * lyr + wr * ryr
    else:
        xr = (lxr + rxr) / 2.0
        yr = (lyr + ryr) / 2.0

    dx = xr - 0.5
    dy = yr - 0.5
    return dx, dy


def gaze_vector_end(
    start_xy: tuple[float, float],
    dx: float,
    dy: float,
    img_w: int,
    img_h: int,
    scale: float = 2.0,
) -> tuple[float, float]:
    sx, sy = start_xy
    vx = dx * img_w * scale
    vy = dy * img_h * scale
    return (float(sx + vx), float(sy + vy))


class GazeEstimatorIrisRatio:
    def __init__(self, cfg: GazeSmoothConfig) -> None:
        self.cfg = cfg
        self._has: bool = False
        self._dx_f: float = 0.0
        self._dy_f: float = 0.0
        self._end_f: tuple[float, float] | None = None

    def estimate_end_point(
        self,
        clm: Landmarks,
        start_xy: tuple[float, float],
        img_w: int,
        img_h: int,
    ) -> tuple[tuple[float, float], float, float]:
        dx, dy = eye_ratio(clm)

        if abs(dx) < self.cfg.deadzone:
            dx = 0.0
        if abs(dy) < self.cfg.deadzone:
            dy = 0.0

        if not self._has:
            self._dx_f, self._dy_f = dx, dy
            self._has = True
        else:
            dx = self._dx_f + float(
                np.clip(dx - self._dx_f, -self.cfg.max_jump, +self.cfg.max_jump),
            )
            dy = self._dy_f + float(
                np.clip(dy - self._dy_f, -self.cfg.max_jump, +self.cfg.max_jump),
            )
            self._dx_f = self.cfg.alpha * dx + (1 - self.cfg.alpha) * self._dx_f
            self._dy_f = self.cfg.alpha * dy + (1 - self.cfg.alpha) * self._dy_f

        dx, dy = self._dx_f, self._dy_f
        end_raw = gaze_vector_end(
            start_xy,
            dx,
            dy,
            img_w=img_w,
            img_h=img_h,
            scale=self.cfg.gaze_scale,
        )

        end_smoothed = smooth_xy(
            self._end_f,
            end_raw,
            alpha=self.cfg.end_alpha,
            max_jump=self.cfg.end_jump_px,
        )
        self._end_f = end_smoothed
        return end_smoothed, dx, dy


class ParentEyeROIBuilder:
    def __init__(self, cfg: ROIConfig) -> None:
        self.cfg = cfg

    @staticmethod
    def _mask_from_hull(
        hull: npt.NDArray[np.int32],
        img_h: int,
        img_w: int,
        dilate_px: int,
    ) -> MaskU8:
        mask = np.zeros((img_h, img_w), dtype=np.uint8)
        cv2.fillConvexPoly(mask, hull, 255)
        k = max(3, int(dilate_px) // 2 * 2 + 1)
        kernel = np.ones((k, k), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        return mask

    def from_mesh(
        self,
        plm: Landmarks,
        offset_xy: tuple[int, int],
        img_h: int,
        img_w: int,
    ) -> tuple[npt.NDArray[np.int32], MaskU8, str]:
        ox, oy = offset_xy
        idxs = LEFT_EYE_CONTOUR + RIGHT_EYE_CONTOUR
        pts = np.array(
            [[plm[i][0] + ox, plm[i][1] + oy] for i in idxs],
            dtype=np.float32,
        )
        pts[:, 0] = np.clip(pts[:, 0], 0, img_w - 1)
        pts[:, 1] = np.clip(pts[:, 1], 0, img_h - 1)
        hull = cv2.convexHull(pts.astype(np.int32))
        mask = self._mask_from_hull(hull, img_h, img_w, self.cfg.mesh_dilate_px)
        return hull, mask, "mesh_eye"

    def from_bbox_fallback(
        self,
        parent_bbox_xyxy: BBox,
        img_h: int,
        img_w: int,
    ) -> tuple[npt.NDArray[np.int32], MaskU8, str]:
        x1, y1, x2, y2 = parent_bbox_xyxy
        x1 = float(clamp(x1, 0, img_w - 1))
        x2 = float(clamp(x2, 0, img_w - 1))
        y1 = float(clamp(y1, 0, img_h - 1))
        y2 = float(clamp(y2, 0, img_h - 1))

        bw = max(1.0, x2 - x1)
        bh = max(1.0, y2 - y1)

        rx1 = int(clamp(x1 + 0.15 * bw, 0, img_w - 1))
        rx2 = int(clamp(x1 + 0.85 * bw, 0, img_w - 1))
        ry1 = int(clamp(y1 + 0.18 * bh, 0, img_h - 1))
        ry2 = int(clamp(y1 + 0.55 * bh, 0, img_h - 1))

        mask = np.zeros((img_h, img_w), dtype=np.uint8)
        cx = (rx1 + rx2) // 2
        cy = (ry1 + ry2) // 2
        ax = max(1, (rx2 - rx1) // 2)
        ay = max(1, (ry2 - ry1) // 2)
        cv2.ellipse(mask, (cx, cy), (ax, ay), 0, 0, 360, 255, -1)

        k = max(3, int(self.cfg.bbox_fallback_dilate_px) // 2 * 2 + 1)
        kernel = np.ones((k, k), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

        rect = np.array(
            [[rx1, ry1], [rx2, ry1], [rx2, ry2], [rx1, ry2]],
            dtype=np.int32,
        )
        return rect, mask, "bbox_fallback"


# -----------------------------
# Debug Renderer
# -----------------------------
class DebugRenderer:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        if self.enabled:
            cv2.namedWindow("debug", cv2.WINDOW_NORMAL)

    def close(self) -> None:
        if self.enabled:
            cv2.destroyAllWindows()

    @staticmethod
    def draw_indices(
        img: FrameBGR,
        pts: Landmarks,
        indices: Sequence[int],
        offset: tuple[int, int] = (0, 0),
        color: tuple[int, int, int] = (0, 255, 0),
        radius: int = 2,
    ) -> None:
        ox, oy = offset
        h, w = img.shape[:2]
        for idx in indices:
            x, y, _ = pts[idx]
            px = int(x + ox)
            py = int(y + oy)
            if 0 <= px < w and 0 <= py < h:
                cv2.circle(img, (px, py), radius, color, -1)

    def show(self, dbg: FrameBGR, fps: float) -> bool:
        if not self.enabled:
            return False
        delay_ms = max(1, int(1000.0 / fps))
        cv2.imshow("debug", dbg)
        return (cv2.waitKey(delay_ms) & 0xFF) == 27


# -----------------------------
# Roles
# -----------------------------
class RoleAssignerByArea:
    """
    warmup 구간에서 track별 평균 얼굴 면적을 누적해,
    큰 얼굴 = parent, 작은 얼굴 = child 로 지정
    """

    def __init__(self, warmup_s: float) -> None:
        self.warmup_s = warmup_s
        self.stats: dict[int, dict[str, float]] = {}
        self.assigned: bool = False
        self.parent_id: int | None = None
        self.child_id: int | None = None

    def update_warmup(
        self,
        cur_t: float,
        start_t: float,
        tracks: list[Track],
    ) -> None:
        if cur_t <= start_t + self.warmup_s:
            for x1, y1, x2, y2, tid in tracks:
                area = bbox_area_xyxy((x1, y1, x2, y2))
                st = self.stats.setdefault(tid, {"sum_area": 0.0, "cnt": 0.0})
                st["sum_area"] += area
                st["cnt"] += 1.0

    def maybe_assign(self, cur_t: float, start_t: float) -> None:
        if self.assigned:
            return
        if cur_t < start_t + self.warmup_s:
            return
        if len(self.stats) < 2:
            return

        items: list[tuple[float, float, int]] = []
        for tid, st in self.stats.items():
            if st["cnt"] <= 0:
                continue
            mean_area = st["sum_area"] / st["cnt"]
            items.append((st["cnt"], mean_area, tid))
        items.sort(reverse=True)

        top2 = items[:2]
        if len(top2) != 2:
            return

        if top2[0][1] >= top2[1][1]:
            self.parent_id = top2[0][2]
            self.child_id = top2[1][2]
        else:
            self.parent_id = top2[1][2]
            self.child_id = top2[0][2]

        self.assigned = True


# -----------------------------
# Results
# -----------------------------
@dataclass
class CallResult:
    call_index: int
    call_start: float
    call_end: float
    success: bool
    latency_s: float | None
    gaze_duration_s: float


# -----------------------------
# Window Analyzer
# -----------------------------
class WindowAnalyzer:
    def __init__(
        self,
        detector: FaceDetectorMP,
        facemesh: FaceMeshMP,
        track_cfg: TrackConfig,
        role_cfg: RoleAssignConfig,
        roi_cfg: ROIConfig,
        gaze_cfg: GazeSmoothConfig,
        contact_cfg: ContactConfig,
        analysis_cfg: AnalysisConfig,
        conf_th: float,
        debug_publish: Callable[[FrameBGR], None] | None = None,
    ) -> None:
        self.detector = detector
        self.facemesh = facemesh
        self.tracker = SortTracker(track_cfg)
        self.role_cfg = role_cfg
        self.roi_builder = ParentEyeROIBuilder(roi_cfg)
        self.gaze_estimator = GazeEstimatorIrisRatio(gaze_cfg)
        self.contact_cfg = contact_cfg
        self.analysis_cfg = analysis_cfg
        self.conf_th = conf_th
        self.debug_publish = debug_publish

    def analyze_call(
        self,
        video_path: str,
        call_idx: int,
        call_start: float,
        call_end: float,
    ) -> CallResult:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"비디오 열기 실패: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if self.analysis_cfg.fps_override and self.analysis_cfg.fps_override > 0:
            fps = self.analysis_cfg.fps_override
        fps = fps if fps and fps > 1e-3 else 30.0
        dt = 1.0 / fps

        start_t = max(0.0, call_end)
        end_t = call_end + self.analysis_cfg.window_s
        cap.set(cv2.CAP_PROP_POS_MSEC, start_t * 1000.0)

        role_assigner = RoleAssignerByArea(self.role_cfg.warmup_s)

        consec_contact: int = 0
        first_contact_time: float | None = None
        gaze_duration: float = 0.0

        debug = DebugRenderer(self.analysis_cfg.debug)
        frame_idx: int = 0

        # debug 창 OR MJPEG publish 둘 중 하나라도 켜져있으면 dbg 프레임을 만든다
        debug_mode = self.analysis_cfg.debug or (self.debug_publish is not None)

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                frame_idx += 1
                cur_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                cur_t = cur_msec / 1000.0
                if cur_t > end_t:
                    break

                h, w = frame.shape[:2]
                dbg: FrameBGR | None = frame.copy() if debug_mode else None

                # detect + track
                dets = self.detector.detect(frame)
                dets = [d for d in dets if d[4] >= self.conf_th]
                dets_xyxy: list[BBox] = [(d[0], d[1], d[2], d[3]) for d in dets]
                tracks = self.tracker.update(dets_xyxy)

                role_assigner.update_warmup(cur_t, start_t, tracks)
                role_assigner.maybe_assign(cur_t, start_t)

                if debug_mode and dbg is not None:
                    msg = (
                        f"t={cur_t:.2f}s tracks={len(tracks)} "
                        f"role={role_assigner.assigned}"
                    )
                    cv2.putText(
                        dbg,
                        msg,
                        (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2,
                    )
                    for x1, y1, x2, y2, tid in tracks:
                        cv2.rectangle(
                            dbg,
                            (int(x1), int(y1)),
                            (int(x2), int(y2)),
                            (200, 200, 0),
                            2,
                        )
                        cv2.putText(
                            dbg,
                            f"id={tid}",
                            (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (200, 200, 0),
                            2,
                        )

                # role 미할당: 계속 publish 해야 /debug/mjpeg가 무한로딩 안 함
                if not role_assigner.assigned:
                    if debug_mode and dbg is not None:
                        cv2.putText(
                            dbg,
                            "role not assigned",
                            (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )

                    if self.debug_publish is not None and dbg is not None:
                        self.debug_publish(dbg)

                    if (
                        self.analysis_cfg.debug
                        and dbg is not None
                        and debug.show(dbg, fps)
                    ):
                        break
                    continue

                parent_id = role_assigner.parent_id
                child_id = role_assigner.child_id
                if parent_id is None or child_id is None:
                    continue

                # locate bboxes
                parent_bbox: BBox | None = None
                child_bbox: BBox | None = None
                for x1, y1, x2, y2, tid in tracks:
                    if tid == parent_id:
                        parent_bbox = (x1, y1, x2, y2)
                    elif tid == child_id:
                        child_bbox = (x1, y1, x2, y2)

                # tracking lost도 publish
                if parent_bbox is None or child_bbox is None:
                    consec_contact = 0

                    if debug_mode and dbg is not None:
                        cv2.putText(
                            dbg,
                            "tracking lost",
                            (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )

                    if self.debug_publish is not None and dbg is not None:
                        self.debug_publish(dbg)

                    if (
                        self.analysis_cfg.debug
                        and dbg is not None
                        and debug.show(dbg, fps)
                    ):
                        break
                    continue

                # crop
                parent_crop, (pox, poy) = crop_face_square(
                    frame, parent_bbox, margin=0.25
                )
                child_crop, (cox, coy) = crop_face_square(
                    frame, child_bbox, margin=0.40
                )

                # facemesh
                plm = self.facemesh.landmarks(parent_crop)  # optional
                clm = self.facemesh.landmarks(child_crop)  # required
                if clm is None:
                    consec_contact = 0

                    if debug_mode and dbg is not None:
                        cv2.putText(
                            dbg,
                            "child facemesh failed",
                            (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )

                    if self.debug_publish is not None and dbg is not None:
                        self.debug_publish(dbg)

                    if (
                        self.analysis_cfg.debug
                        and dbg is not None
                        and debug.show(dbg, fps)
                    ):
                        break
                    continue

                # child gaze start point: outer corners mid
                cleft_outer = (
                    clm[LEFT_EYE_OUTER][0] + cox,
                    clm[LEFT_EYE_OUTER][1] + coy,
                )
                cright_outer = (
                    clm[RIGHT_EYE_OUTER][0] + cox,
                    clm[RIGHT_EYE_OUTER][1] + coy,
                )
                sx = (cleft_outer[0] + cright_outer[0]) / 2.0
                sy = (cleft_outer[1] + cright_outer[1]) / 2.0

                end_pt, dx, dy = self.gaze_estimator.estimate_end_point(
                    clm,
                    (sx, sy),
                    img_w=w,
                    img_h=h,
                )

                # parent ROI
                if plm is not None:
                    hull, eye_mask, roi_mode = self.roi_builder.from_mesh(
                        plm,
                        (pox, poy),
                        img_h=h,
                        img_w=w,
                    )
                else:
                    hull, eye_mask, roi_mode = self.roi_builder.from_bbox_fallback(
                        parent_bbox,
                        img_h=h,
                        img_w=w,
                    )

                contact = contact_by_raycast(
                    eye_mask,
                    (sx, sy),
                    end_pt,
                    n_samples=self.contact_cfg.raycast_samples,
                )

                if contact:
                    consec_contact += 1
                    gaze_duration += dt
                    if (
                        first_contact_time is None
                        and consec_contact >= self.contact_cfg.min_contact_frames
                    ):
                        first_contact_time = cur_t
                    status_msg = f"CONTACT ({roi_mode})"
                    status_color = (0, 255, 0)
                else:
                    consec_contact = 0
                    status_msg = f"no contact ({roi_mode})"
                    status_color = (0, 255, 255)

                # debug overlay는 debug_mode 기준으로 (스트리밍에도 뜨게)
                if debug_mode and dbg is not None:
                    px1, py1, px2, py2 = map(int, parent_bbox)
                    cx1, cy1, cx2, cy2 = map(int, child_bbox)

                    cv2.rectangle(dbg, (px1, py1), (px2, py2), (255, 255, 0), 2)
                    cv2.putText(
                        dbg,
                        "P",
                        (px1, py1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (255, 255, 0),
                        2,
                    )

                    cv2.rectangle(dbg, (cx1, cy1), (cx2, cy2), (0, 255, 255), 2)
                    cv2.putText(
                        dbg,
                        "C",
                        (cx1, cy1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 255, 255),
                        2,
                    )

                    overlay = dbg.copy()
                    overlay[eye_mask > 0] = (0, 255, 0)
                    dbg = cv2.addWeighted(overlay, 0.25, dbg, 0.75, 0)

                    cv2.polylines(dbg, [hull], True, (0, 255, 0), 2)

                    DebugRenderer.draw_indices(
                        dbg,
                        clm,
                        LEFT_IRIS,
                        offset=(cox, coy),
                        color=(255, 0, 255),
                        radius=2,
                    )
                    DebugRenderer.draw_indices(
                        dbg,
                        clm,
                        RIGHT_IRIS,
                        offset=(cox, coy),
                        color=(255, 0, 255),
                        radius=2,
                    )

                    cv2.circle(dbg, (int(sx), int(sy)), 3, (255, 0, 0), -1)
                    cv2.circle(
                        dbg,
                        (int(end_pt[0]), int(end_pt[1])),
                        5,
                        (0, 0, 255),
                        -1,
                    )
                    cv2.line(
                        dbg,
                        (int(sx), int(sy)),
                        (int(end_pt[0]), int(end_pt[1])),
                        (0, 0, 255),
                        2,
                    )

                    status_line = (
                        f"{status_msg} consec={consec_contact} "
                        f"dx={dx:+.3f} dy={dy:+.3f}"
                    )
                    cv2.putText(
                        dbg,
                        status_line,
                        (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        status_color,
                        2,
                    )

                # 매 프레임 publish (가장 중요)
                if self.debug_publish is not None and dbg is not None:
                    self.debug_publish(dbg)

                # 로컬 GUI debug 창은 debug=True일 때만
                if self.analysis_cfg.debug and dbg is not None and debug.show(dbg, fps):
                    break

        finally:
            cap.release()
            debug.close()

        success = first_contact_time is not None
        latency = (first_contact_time - call_end) if success else None

        return CallResult(
            call_index=call_idx,
            call_start=call_start,
            call_end=call_end,
            success=success,
            latency_s=latency,
            gaze_duration_s=float(gaze_duration),
        )

    def _publish_dbg(self, dbg: FrameBGR | None) -> None:
        if self.debug_publish is not None and dbg is not None:
            self.debug_publish(dbg)


# -----------------------------
# Video Analyzer (orchestration)
# -----------------------------
class VideoAnalyzer:
    def __init__(
        self,
        vad_cfg: VADConfig,
        face_cfg: FaceDetConfig,
        track_cfg: TrackConfig,
        role_cfg: RoleAssignConfig,
        roi_cfg: ROIConfig,
        gaze_cfg: GazeSmoothConfig,
        contact_cfg: ContactConfig,
        analysis_cfg: AnalysisConfig,
        conf_th: float,
    ) -> None:
        self.vad_cfg = vad_cfg
        self.analysis_cfg = analysis_cfg

        self.vad = SileroVAD(vad_cfg)
        self.detector = FaceDetectorMP(face_cfg)
        self.facemesh = FaceMeshMP()

        self.window_analyzer = WindowAnalyzer(
            detector=self.detector,
            facemesh=self.facemesh,
            track_cfg=track_cfg,
            role_cfg=role_cfg,
            roi_cfg=roi_cfg,
            gaze_cfg=gaze_cfg,
            contact_cfg=contact_cfg,
            analysis_cfg=analysis_cfg,
            conf_th=conf_th,
        )

    def analyze(self, video_path: str) -> dict[str, Any]:
        tmp_dir = os.path.join(
            os.path.dirname(os.path.abspath(video_path)),
            self.vad_cfg.tmp_dirname,
        )

        segs = self.vad.segments_from_video(video_path, tmp_dir=tmp_dir)
        segs = merge_close_segments(segs, gap_s=self.vad_cfg.merge_gap_s)

        logger.info("VAD segs: %d (show first 5) %s", len(segs), segs[:5])

        results: list[CallResult] = []
        for i, (s, e) in enumerate(segs, start=1):
            r = self.window_analyzer.analyze_call(
                video_path,
                call_idx=i,
                call_start=s,
                call_end=e,
            )
            results.append(r)

        total_calls = len(results)
        success_calls = sum(1 for r in results if r.success)
        total_gaze = sum(r.gaze_duration_s for r in results)
        latencies = [r.latency_s for r in results if r.latency_s is not None]
        avg_latency = float(np.mean(latencies)) if latencies else None

        params = {
            "window_s": self.analysis_cfg.window_s,
            "vad_merge_gap_s": self.vad_cfg.merge_gap_s,
            "vad_min_speech_ms": self.vad_cfg.min_speech_ms,
            "vad_min_silence_ms": self.vad_cfg.min_silence_ms,
            "min_contact_frames": self.window_analyzer.contact_cfg.min_contact_frames,
            "warmup_s": self.window_analyzer.role_cfg.warmup_s,
            "face_det_conf_th": self.window_analyzer.conf_th,
        }

        return {
            "video": os.path.basename(video_path),
            "params": params,
            "summary": {
                "success_count": int(success_calls),
                "total_call_count": int(total_calls),
                "avg_latency_s": avg_latency,
                "total_gaze_duration_s": float(total_gaze),
            },
            "per_call": [
                {
                    "call_index": r.call_index,
                    "call_start_s": r.call_start,
                    "call_end_s": r.call_end,
                    "success": r.success,
                    "latency_s": r.latency_s,
                    "gaze_duration_s": r.gaze_duration_s,
                }
                for r in results
            ],
        }


# -----------------------------
# Service helper (FastAPI용)
# -----------------------------
def build_analyzer(
    window_s: float = 5.0,
    vad_merge_gap: float = 0.3,
    vad_min_speech_ms: int = 250,
    vad_min_silence_ms: int = 250,
    min_contact_frames: int = 3,
    warmup_s: float = 1.0,
    conf: float = 0.6,
    debug: bool = False,
    fps_override: float | None = None,
) -> VideoAnalyzer:
    vad_cfg = VADConfig(
        sr=16000,
        min_speech_ms=vad_min_speech_ms,
        min_silence_ms=vad_min_silence_ms,
        merge_gap_s=vad_merge_gap,
    )
    face_cfg = FaceDetConfig(min_conf=conf, model_selection=0)
    track_cfg = TrackConfig(max_age=8, min_hits=2, iou_threshold=0.3)
    role_cfg = RoleAssignConfig(warmup_s=warmup_s)
    roi_cfg = ROIConfig(mesh_dilate_px=14, bbox_fallback_dilate_px=28)
    gaze_cfg = GazeSmoothConfig()
    contact_cfg = ContactConfig(
        min_contact_frames=min_contact_frames,
        raycast_samples=11,
    )
    analysis_cfg = AnalysisConfig(
        window_s=window_s,
        debug=debug,
        fps_override=fps_override,
    )

    return VideoAnalyzer(
        vad_cfg=vad_cfg,
        face_cfg=face_cfg,
        track_cfg=track_cfg,
        role_cfg=role_cfg,
        roi_cfg=roi_cfg,
        gaze_cfg=gaze_cfg,
        contact_cfg=contact_cfg,
        analysis_cfg=analysis_cfg,
        conf_th=conf,
    )


def analyze_video(video_path: str, analyzer: VideoAnalyzer) -> dict[str, Any]:
    t0 = time.time()
    out = analyzer.analyze(video_path)
    out["elapsed_s"] = float(time.time() - t0)
    return out
