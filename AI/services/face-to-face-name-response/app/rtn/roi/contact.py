from app.rtn.types import MaskU8
from app.rtn.utils import clamp


def contact_by_raycast(
    eye_mask: MaskU8,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    n_samples: int = 11,
) -> bool:
    """
    eye_mask(ROI) 위로 start->end 선분을 n_samples로 샘플링하며
    한 점이라도 마스크(>0)에 닿으면 contact=True.
    """
    h, w = eye_mask.shape[:2]
    sx, sy = start_xy
    ex, ey = end_xy

    if n_samples < 2:
        n_samples = 2

    for i in range(n_samples):
        t = i / (n_samples - 1)
        x = int(clamp(sx + (ex - sx) * t, 0, w - 1))
        y = int(clamp(sy + (ey - sy) * t, 0, h - 1))
        if eye_mask[y, x] > 0:
            return True
    return False
