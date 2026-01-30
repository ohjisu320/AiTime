import time

from src.contracts.context import ROI, QualityFlag, RunContext, StageOutput
from src.pipelines.stages.base import Stage

BBox = tuple[int, int, int, int]


class ROIPayload(dict):
    """
    payload keys:
      - frame_wh: (W,H)
      - face_bboxes: list[BBox]
    """


class ROIOut(dict):
    """
    payload keys:
      - roi1_has_face: bool
      - roi2_has_face: bool
      - roi1_overlap_max: float
      - roi2_overlap_max: float
    """


def _roi_to_px(roi: ROI, W: int, H: int) -> tuple[int, int, int, int]:
    x0 = int(roi.x0 * W)
    y0 = int(roi.y0 * H)
    x1 = int(roi.x1 * W)
    y1 = int(roi.y1 * H)
    return x0, y0, x1, y1


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0 = max(ax0, bx0)
    iy0 = max(ay0, by0)
    ix1 = min(ax1, bx1)
    iy1 = min(ay1, by1)
    iw = max(0, ix1 - ix0)
    ih = max(0, iy1 - iy0)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    a_area = max(0, ax1 - ax0) * max(0, ay1 - ay0)
    b_area = max(0, bx1 - bx0) * max(0, by1 - by0)
    union = max(1, a_area + b_area - inter)
    return float(inter / union)


class ROIValidateStage(Stage[ROIPayload, ROIOut]):
    name = "roi_validate"

    def run(self, ctx: RunContext, payload: ROIPayload) -> StageOutput[ROIOut]:
        t0 = time.perf_counter()
        flags: list[QualityFlag] = []

        W, H = payload["frame_wh"]
        bboxes: list[BBox] = payload["face_bboxes"]

        roi1_px = _roi_to_px(ctx.roi_1, W, H)
        roi2_px = _roi_to_px(ctx.roi_2, W, H)

        roi1_max = 0.0
        roi2_max = 0.0
        for bb in bboxes:
            roi1_max = max(roi1_max, _iou(roi1_px, bb))
            roi2_max = max(roi2_max, _iou(roi2_px, bb))

        roi1_has = roi1_max > 0.01  # tiny threshold; tune later
        roi2_has = roi2_max > 0.01

        if not roi1_has:
            flags.append(QualityFlag.ROI_FACE_MISSING_1)
        if not roi2_has:
            flags.append(QualityFlag.ROI_FACE_MISSING_2)

        out: ROIOut = {
            "roi1_has_face": bool(roi1_has),
            "roi2_has_face": bool(roi2_has),
            "roi1_overlap_max": float(roi1_max),
            "roi2_overlap_max": float(roi2_max),
        }
        metrics = self._metrics(
            t0, success=True, roi1_overlap=roi1_max, roi2_overlap=roi2_max
        )
        return StageOutput(payload=out, stage_metrics=metrics, quality_flags=flags)
