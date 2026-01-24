import cv2
import numpy as np
import numpy.typing as npt

from app.rtn.config import ROIConfig
from app.rtn.indices import LEFT_EYE_CONTOUR, RIGHT_EYE_CONTOUR
from app.rtn.types import BBox, Landmarks, MaskU8
from app.rtn.utils import clamp


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
            [[plm[i][0] + ox, plm[i][1] + oy] for i in idxs], dtype=np.float32
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

        # 얼굴 bbox 내부에서 "눈이 있을 법한" 상단 영역을 ellipse로 근사
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
            [[rx1, ry1], [rx2, ry1], [rx2, ry2], [rx1, ry2]], dtype=np.int32
        )
        return rect, mask, "bbox_fallback"
