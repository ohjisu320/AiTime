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


def _center_in_roi(bb: BBox, roi_px: tuple[int, int, int, int]) -> bool:
    x0, y0, x1, y1 = bb
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    rx0, ry0, rx1, ry1 = roi_px
    return (rx0 <= cx <= rx1) and (ry0 <= cy <= ry1)


class ROIValidateStage(Stage[ROIPayload, ROIOut]):
    name = "roi_validate"

    def run(self, ctx: RunContext, payload: ROIPayload) -> StageOutput[ROIOut]:
        t0 = time.perf_counter()
        flags: list[QualityFlag] = []

        W, H = payload["frame_wh"]
        bboxes: list[BBox] = payload["face_bboxes"]

        roi1_px = _roi_to_px(ctx.roi_1, W, H)
        roi2_px = _roi_to_px(ctx.roi_2, W, H)

        roi1_has = any(_center_in_roi(bb, roi1_px) for bb in bboxes)
        roi2_has = any(_center_in_roi(bb, roi2_px) for bb in bboxes)

        if not roi1_has:
            flags.append(QualityFlag.ROI_FACE_MISSING_1)
        if not roi2_has:
            flags.append(QualityFlag.ROI_FACE_MISSING_2)

        out: ROIOut = {
            "roi1_has_face": bool(roi1_has),
            "roi2_has_face": bool(roi2_has),
            "roi1_overlap_max": 1.0 if roi1_has else 0.0,  # 호환용
            "roi2_overlap_max": 1.0 if roi2_has else 0.0,
        }
        metrics = self._metrics(t0, success=True, roi1_has=roi1_has, roi2_has=roi2_has)
        return StageOutput(payload=out, stage_metrics=metrics, quality_flags=flags)
