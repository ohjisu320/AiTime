import numpy as np

from app.rtn.types import BBox, FrameBGR


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
