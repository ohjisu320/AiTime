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
    """홍채(iris) landmark들의 평균으로 iris 중심점을 계산한다(픽셀 좌표)."""
    xs = [pts[i][0] for i in iris_indices]
    ys = [pts[i][1] for i in iris_indices]
    return float(np.mean(xs)), float(np.mean(ys))


def eye_ratio(pts: Landmarks) -> tuple[float, float]:
    """
    iris가 눈(eye contour) 내부에서 어디에 위치하는지 비율로 dx/dy를 추정한다.

    아이디어(2D 휴리스틱):
    - 눈 윤곽(contour)의 bbox를 기준 좌표계로 두고,
      iris 중심이 그 안에서 (x,y) 비율로 어디에 있는지 계산한다.
      * xr,yr ∈ [0,1] 근처
      * dx = xr - 0.5, dy = yr - 0.5  -> 중심 대비 오프셋
    - dx/dy는 정규화된 값(픽셀 아님)이며, 보통 [-0.5, +0.5] 범위 근처에서 움직인다.

    한계:
    - head pose/카메라 각/개인 눈 형태에 따라 절대 시선 각도로 해석하기는 어렵다.
      여기서는 '상대적 시선 방향'을 안정적으로 얻을 수 있음
    """

    def one_eye(
        iris_idx: Sequence[int],
        contour_idx: Sequence[int],
    ) -> tuple[float, float, float]:
        # 한쪽 눈에 대해:
        # - iris 중심(cx,cy)
        # - eye contour bbox(x0,x1,y0,y1)
        # - xr,yr: bbox 내 상대 위치 비율
        # - q: bbox 면적(가중치로 사용, 눈이 더 크게/잘 잡힌 쪽에 비중 높임)
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

    # 두 눈을 합치는 정책:
    # - 한쪽 눈이 가려지거나 mesh가 흔들리면 bbox가 작게 잡힐 수 있으므로
    #   bbox 면적(q)을 가중치로 사용해 더 신뢰할 만한 쪽에 비중을 둠
    qsum = lq + rq
    if qsum > 1e-6:
        wl = lq / qsum
        wr = rq / qsum
        xr = wl * lxr + wr * rxr
        yr = wl * lyr + wr * ryr
    else:
        # 극단적으로 둘 다 작으면(비정상/노이즈) 단순 평균으로 fallback
        xr = (lxr + rxr) / 2.0
        yr = (lyr + ryr) / 2.0

    # 중심(0.5,0.5) 대비 오프셋: dx,dy는 "정규화된 방향성" 값
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
    """
    (정규화된) dx/dy를 픽셀 스케일 벡터로 바꿔 start_xy에서의 끝점 생성

    - dx는 가로 방향 비율 오프셋 -> img_w를 곱해 픽셀 이동량으로 변환
    - dy는 세로 방향 비율 오프셋 -> img_h를 곱해 픽셀 이동량으로 변환
    - scale은 시선 벡터를 얼마나 '길게' 그릴지(시각화/ROI hit-test 민감도)에 영향
    """
    sx, sy = start_xy
    vx = dx * img_w * scale
    vy = dy * img_h * scale
    return (float(sx + vx), float(sy + vy))


class GazeEstimatorIrisRatio:
    """
    iris ratio 기반 2D 시선 추정기(캘리브레이션 없는 휴리스틱)

    출력
    - dx/dy: eye_ratio에서 나온 정규화 오프셋(픽셀 아님)
    - end_point: start_xy에서 dx/dy를 픽셀 벡터로 확장한 끝점(픽셀 좌표)

    안정화 기법
    - deadzone: 작은 흔들림을 0으로(미세 노이즈/미세 떨림 억제)
    - max_jump + alpha: dx/dy에 대한 jump clamp + 지수평활(IIR)
    - end_alpha/end_jump_px: end point(픽셀)도 별도 smoothing
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
        # 1) iris ratio로 정규화된 방향(dx,dy) 추정
        dx, dy = eye_ratio(clm)

        # deadzone : 거의 중앙을 보는 것처럼 보이는 작은 값은 0(떨림 억제)
        if abs(dx) < self.cfg.deadzone:
            dx = 0.0
        if abs(dy) < self.cfg.deadzone:
            dy = 0.0

        # dx/dy smoothing
        # - 프레임별 스파이크를 jump clamp로 제한
        # - 이후 IIR(alpha)로 저역통과(부드럽게, 대신 반응 지연)
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
        # dx/dy(정규화)를 픽셀 벡터로 확장
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
        # call 단위 분석에서 이전 상태(필터)가 다음 구간에 영향을 주지 않도록 초기화
        self._has = False
        self._dx_f = 0.0
        self._dy_f = 0.0
        self._end_f = None
