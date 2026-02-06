"""
ByteTrack - 저신뢰도 검출 활용 강화 트래커.

SORT의 한계:
- 고신뢰도 검출만 사용 → 측면/가림 시 ID 단절

ByteTrack 개선:
1. 1차: 고신뢰도 검출 ↔ 트랙 매칭
2. 2차: 미매칭 트랙 ↔ 저신뢰도 검출 매칭
→ 검출 신뢰도가 떨어져도 트랙 유지 가능

참고: https://arxiv.org/abs/2110.06864
"""

import math

import numpy as np
import numpy.typing as npt

from app.rtn.config import TrackConfig
from app.rtn.types import BBox, Track
from app.rtn.utils import iou_xyxy

try:
    from scipy.optimize import linear_sum_assignment

    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False


class KalmanBoxTracker:
    """Kalman Filter 기반 단일 객체 추적기 (SORT와 동일)."""

    count: int = 0

    def __init__(self, bbox_xyxy: BBox, score: float = 1.0) -> None:
        KalmanBoxTracker.count += 1
        self.id: int = KalmanBoxTracker.count
        self.score: float = score

        x1, y1, x2, y2 = bbox_xyxy
        w = x2 - x1
        h = y2 - y1
        cx = x1 + w / 2.0
        cy = y1 + h / 2.0
        s = w * h
        r = w / (h + 1e-9)

        self.x: npt.NDArray[np.float32] = np.array(
            [[cx], [cy], [s], [r], [0.0], [0.0], [0.0]],
            dtype=np.float32,
        )

        self.P: npt.NDArray[np.float32] = np.eye(7, dtype=np.float32) * 10.0
        self.F: npt.NDArray[np.float32] = np.eye(7, dtype=np.float32)
        self.F[0, 4] = 1.0
        self.F[1, 5] = 1.0
        self.F[2, 6] = 1.0
        self.Q: npt.NDArray[np.float32] = np.eye(7, dtype=np.float32) * 0.01
        self.H: npt.NDArray[np.float32] = np.zeros((4, 7), dtype=np.float32)
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0
        self.H[2, 2] = 1.0
        self.H[3, 3] = 1.0
        self.R: npt.NDArray[np.float32] = np.eye(4, dtype=np.float32) * 1.0

        self.time_since_update: int = 0
        self.hits: int = 1
        self.hit_streak: int = 1
        self.age: int = 0

    def predict(self) -> BBox:
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        self.age += 1
        self.time_since_update += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        return self.get_state_bbox()

    def update(self, bbox_xyxy: BBox, score: float = 1.0) -> None:
        x1, y1, x2, y2 = bbox_xyxy
        w = x2 - x1
        h = y2 - y1
        cx = x1 + w / 2.0
        cy = y1 + h / 2.0
        s = w * h
        r = w / (h + 1e-9)

        z: npt.NDArray[np.float32] = np.array([[cx], [cy], [s], [r]], dtype=np.float32)

        Hx = self.H @ self.x
        y = z - Hx
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S + 1e-9 * np.eye(4))

        self.x = self.x + (K @ y)
        self.P = (np.eye(7, dtype=np.float32) - K @ self.H) @ self.P

        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1
        self.score = score

    def get_state_bbox(self) -> BBox:
        cx = float(self.x[0, 0])
        cy = float(self.x[1, 0])
        s = float(self.x[2, 0])
        r = float(self.x[3, 0])

        w = math.sqrt(abs(s * r))
        h = abs(s) / (w + 1e-9)
        x1 = cx - w / 2.0
        y1 = cy - h / 2.0
        x2 = cx + w / 2.0
        y2 = cy + h / 2.0
        return (x1, y1, x2, y2)


class ByteTracker:
    """
    ByteTrack: 2단계 매칭으로 저신뢰도 검출도 활용.

    SORT 대비 개선:
    - 1차: 고신뢰도(>=high_thresh) 검출 ↔ 모든 트랙 매칭
    - 2차: 미매칭 트랙 ↔ 저신뢰도(>=low_thresh, <high_thresh) 검출 매칭
    → 측면/가림으로 검출 점수가 떨어져도 트랙 유지
    """

    def __init__(self, cfg: TrackConfig) -> None:
        self.cfg = cfg
        self.trackers: list[KalmanBoxTracker] = []
        self.frame_count: int = 0

    def update(
        self,
        dets_with_scores: list[tuple[BBox, float]],
    ) -> list[Track]:
        """
        Args:
            dets_with_scores: [(bbox, score), ...] - 점수 포함 검출 결과

        Returns:
            tracks: [(x1, y1, x2, y2, id), ...]
        """
        self.frame_count += 1

        # 검출을 고/저신뢰도로 분리
        high_dets: list[tuple[int, BBox, float]] = []
        low_dets: list[tuple[int, BBox, float]] = []

        for i, (bbox, score) in enumerate(dets_with_scores):
            if score >= self.cfg.high_thresh:
                high_dets.append((i, bbox, score))
            elif score >= self.cfg.low_thresh:
                low_dets.append((i, bbox, score))

        # 예측
        for trk in self.trackers:
            trk.predict()

        # 1차 매칭: 고신뢰도 검출 ↔ 모든 트랙
        high_bboxes = [d[1] for d in high_dets]
        trk_bboxes = [trk.get_state_bbox() for trk in self.trackers]

        matched1, unmatched_dets1, unmatched_trks1 = self._associate(
            high_bboxes, trk_bboxes, self.cfg.iou_threshold
        )

        for det_idx, trk_idx in matched1:
            self.trackers[trk_idx].update(high_dets[det_idx][1], high_dets[det_idx][2])

        # 2차 매칭: 미매칭 트랙 ↔ 저신뢰도 검출
        if low_dets and unmatched_trks1:
            low_bboxes = [d[1] for d in low_dets]
            remain_trk_bboxes = [
                self.trackers[i].get_state_bbox() for i in unmatched_trks1
            ]

            matched2, _, still_unmatched_trks = self._associate(
                low_bboxes, remain_trk_bboxes, self.cfg.second_iou_thresh
            )

            for det_idx, rel_trk_idx in matched2:
                abs_trk_idx = unmatched_trks1[rel_trk_idx]
                self.trackers[abs_trk_idx].update(
                    low_dets[det_idx][1], low_dets[det_idx][2]
                )

            # 실제 미매칭 트랙 업데이트
            unmatched_trks1 = [unmatched_trks1[i] for i in still_unmatched_trks]

        # 미매칭 고신뢰도 검출 → 새 트랙 생성
        for det_idx in unmatched_dets1:
            self.trackers.append(
                KalmanBoxTracker(high_dets[det_idx][1], high_dets[det_idx][2])
            )

        # 오래된 트랙 제거
        self.trackers = [
            t for t in self.trackers if t.time_since_update <= self.cfg.max_age
        ]

        # 출력
        outputs: list[Track] = []
        for trk in self.trackers:
            if trk.hits >= self.cfg.min_hits or self.frame_count <= self.cfg.min_hits:
                b = trk.get_state_bbox()
                outputs.append((b[0], b[1], b[2], b[3], trk.id))
        return outputs

    def update_simple(self, dets_xyxy: list[BBox]) -> list[Track]:
        """SORT 호환 인터페이스 (점수 없이 bbox만 받음)."""
        dets_with_scores = [(bbox, 1.0) for bbox in dets_xyxy]
        return self.update(dets_with_scores)

    def _associate(
        self,
        dets: list[BBox],
        preds: list[BBox],
        iou_thresh: float,
    ) -> tuple[list[tuple[int, int]], list[int], list[int]]:
        """IoU 기반 매칭."""
        if len(preds) == 0:
            return [], list(range(len(dets))), []
        if len(dets) == 0:
            return [], [], list(range(len(preds)))

        iou_mat = np.zeros((len(dets), len(preds)), dtype=np.float32)
        for d, det in enumerate(dets):
            for t, pr in enumerate(preds):
                iou_mat[d, t] = iou_xyxy(det, pr)

        matched: list[tuple[int, int]] = []

        if SCIPY_OK:
            cost = 1.0 - iou_mat
            r, c = linear_sum_assignment(cost)
            for rr, cc in zip(r, c, strict=False):
                if iou_mat[rr, cc] >= iou_thresh:
                    matched.append((rr, cc))
            matched_dets = {m[0] for m in matched}
            matched_trks = {m[1] for m in matched}
            unmatched_dets = [i for i in range(len(dets)) if i not in matched_dets]
            unmatched_trks = [i for i in range(len(preds)) if i not in matched_trks]
        else:
            # Greedy fallback
            pairs = [
                (float(iou_mat[d, t]), d, t)
                for d in range(len(dets))
                for t in range(len(preds))
            ]
            pairs.sort(reverse=True, key=lambda x: x[0])
            used_d: set[int] = set()
            used_t: set[int] = set()
            for iouv, d, t in pairs:
                if iouv < iou_thresh:
                    break
                if d in used_d or t in used_t:
                    continue
                matched.append((d, t))
                used_d.add(d)
                used_t.add(t)
            unmatched_dets = [i for i in range(len(dets)) if i not in used_d]
            unmatched_trks = [i for i in range(len(preds)) if i not in used_t]

        return matched, unmatched_dets, unmatched_trks

    def reset(self) -> None:
        """트래커 상태 초기화."""
        self.trackers = []
        self.frame_count = 0
        KalmanBoxTracker.count = 0
