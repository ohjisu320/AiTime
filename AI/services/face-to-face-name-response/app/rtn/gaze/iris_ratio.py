from collections.abc import Sequence

import numpy as np

from app.rtn.config import GazeSmoothConfig
from app.rtn.indices import (
    LEFT_EYE_CONTOUR,
    LEFT_IRIS,
    RIGHT_EYE_CONTOUR,
    RIGHT_IRIS,
)
from app.rtn.types import Landmarks
from app.rtn.utils import smooth_xy


def iris_center(pts: Landmarks, iris_indices: Sequence[int]) -> tuple[float, float]:
    xs = [pts[i][0] for i in iris_indices]
    ys = [pts[i][1] for i in iris_indices]
    return float(np.mean(xs)), float(np.mean(ys))


def eye_ratio(pts: Landmarks) -> tuple[float, float]:
    """
    두 눈(좌/우) iris 중심이
    eye contour bbox 내에서
    어느 비율에 위치하는지로 dx/dy 산출.
    dx,dy는 [-0.5, +0.5] 근처.
    """

    def one_eye(
        iris_idx: Sequence[int],
        contour_idx: Sequence[int],
    ) -> tuple[float, float, float]:
        cx, cy = iris_center(pts, iris_idx)
        eye = np.array([[pts[i][0], pts[i][1]] for i in contour_idx], dtype=np.float32)
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
    return float(dx), float(dy)


def gaze_vector_end(
    start_xy: tuple[float, float],
    dx: float,
    dy: float,
    img_w: int,
    img_h: int,
    scale: float = 1.6,
) -> tuple[float, float]:
    sx, sy = start_xy
    vx = dx * img_w * scale
    vy = dy * img_h * scale
    return (float(sx + vx), float(sy + vy))


class GazeEstimatorIrisRatio:
    """
    2D 휴리스틱:
    - dx/dy: iris ratio 기반
    - low-pass + jump clamp
    - end point도 픽셀 단위로 추가 smoothing
    """

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

        # deadzone
        if abs(dx) < self.cfg.deadzone:
            dx = 0.0
        if abs(dy) < self.cfg.deadzone:
            dy = 0.0

        # dx/dy smoothing
        if not self._has:
            self._dx_f, self._dy_f = dx, dy
            self._has = True
        else:
            dx = self._dx_f + float(
                np.clip(dx - self._dx_f, -self.cfg.max_jump, +self.cfg.max_jump)
            )
            dy = self._dy_f + float(
                np.clip(dy - self._dy_f, -self.cfg.max_jump, +self.cfg.max_jump)
            )
            self._dx_f = self.cfg.alpha * dx + (1 - self.cfg.alpha) * self._dx_f
            self._dy_f = self.cfg.alpha * dy + (1 - self.cfg.alpha) * self._dy_f

        dx, dy = self._dx_f, self._dy_f

        # end point (raw)
        end_raw = gaze_vector_end(
            start_xy,
            dx,
            dy,
            img_w=img_w,
            img_h=img_h,
            scale=self.cfg.gaze_scale,
        )

        # end point smoothing (pixel-jump clamp)
        end_smoothed = smooth_xy(
            self._end_f,
            end_raw,
            alpha=self.cfg.end_alpha,
            max_jump=self.cfg.end_jump_px,
        )
        self._end_f = end_smoothed
        return end_smoothed, dx, dy

    def reset(self) -> None:
        self._has = False
        self._dx_f = 0.0
        self._dy_f = 0.0
        self._end_f = None
