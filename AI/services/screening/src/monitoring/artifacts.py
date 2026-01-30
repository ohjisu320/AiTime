import json
import random
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from src.contracts.context import ROI

BBox = tuple[int, int, int, int]


def _roi_to_px(roi: ROI, W: int, H: int) -> BBox:
    return (int(roi.x0 * W), int(roi.y0 * H), int(roi.x1 * W), int(roi.y1 * H))


@dataclass
class DebugArtifactSaver:
    run_id: str
    base_dir: str
    enabled: bool
    save_fail_only: bool
    sample_rate: float
    save_on_flags: list[str]
    roi_1: ROI
    roi_2: ROI

    # last seen
    last_frame_bgr: np.ndarray | None = None
    last_bboxes: list[BBox] | None = None
    last_ratios: dict | None = None
    last_scores: dict | None = None

    def update_frame(
        self, frame_bgr: np.ndarray, bboxes: list[BBox], ratios: dict, scores: dict
    ) -> None:
        if not self.enabled:
            return
        self.last_frame_bgr = frame_bgr.copy()
        self.last_bboxes = list(bboxes)
        self.last_ratios = dict(ratios)
        self.last_scores = dict(scores)

    def maybe_save(
        self, passed: bool, flags: list[str], failure_reason: str | None, details: dict
    ) -> None:
        if not self.enabled:
            return

        # preflight에서는 mismatch가 없으니 사실상 "fail only"로 처리
        if self.save_fail_only and passed:
            return

        # flag 트리거가 설정돼있으면 그 flag가 있을 때만
        if self.save_on_flags and not any(f in self.save_on_flags for f in flags):
            return

        # 샘플링
        if self.sample_rate < 1.0 and random.random() > self.sample_rate:
            return

        if self.last_frame_bgr is None:
            return

        run_dir = Path(self.base_dir) / "runs" / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        img = self.last_frame_bgr.copy()
        H, W = img.shape[:2]

        # draw ROIs
        r1 = _roi_to_px(self.roi_1, W, H)
        r2 = _roi_to_px(self.roi_2, W, H)
        cv2.rectangle(img, (r1[0], r1[1]), (r1[2], r1[3]), (0, 255, 0), 2)
        cv2.rectangle(img, (r2[0], r2[1]), (r2[2], r2[3]), (0, 255, 0), 2)

        # draw faces
        if self.last_bboxes:
            for x0, y0, x1, y1 in self.last_bboxes:
                cv2.rectangle(img, (x0, y0), (x1, y1), (255, 0, 0), 2)

        # draw text
        text1 = f"passed={passed} reason={failure_reason}"
        text2 = f"flags={','.join(flags)}"
        cv2.putText(
            img, text1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2
        )
        cv2.putText(
            img, text2, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        out_img = run_dir / ("pass.png" if passed else "fail.png")
        cv2.imwrite(str(out_img), img)

        # save json summary
        summary = {
            "passed": passed,
            "failure_reason": failure_reason,
            "flags": flags,
            "ratios": self.last_ratios or {},
            "scores": self.last_scores or {},
            "details": details,
        }
        (run_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
