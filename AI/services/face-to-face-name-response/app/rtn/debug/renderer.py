from collections.abc import Sequence

import cv2

from app.rtn.types import FrameBGR, Landmarks


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
        delay_ms = max(1, int(1000.0 / max(1e-6, fps)))
        cv2.imshow("debug", dbg)
        return (cv2.waitKey(delay_ms) & 0xFF) == 27
