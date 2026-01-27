"""
간단한 SORT(SIMPLE ONLINE AND REALTIME TRACKING) 구현.

- Kalman Filter로 bbox 상태를 예측/갱신하고,
- detection ↔ prediction 매칭은 IoU 기반으로 수행한다.
- SciPy가 있으면 Hungarian(최적 할당), 없으면 greedy(근사)로 fallback한다.

주의:
- appearance(feature) 없이 IoU만 쓰므로 두 객체가 겹치거나 교차하면 ID-switch 발생 가능
"""

import math

import numpy as np
import numpy.typing as npt

from app.rtn.config import TrackConfig
from app.rtn.types import BBox, Track
from app.rtn.utils import iou_xyxy

# scipy는 SORT 매칭(헝가리안)에 쓰고, 없으면 greedy fallback
try:
    from scipy.optimize import linear_sum_assignment

    SCIPY_OK = True
except Exception:
    SCIPY_OK = False


class KalmanBoxTracker:
    """
    state: [cx, cy, s, r, vx, vy, vs]^T
    - cx, cy: 중심
    - s: area(면적)
    - r: aspect ratio(가로/세로 비)
    - vx, vy, vs: 속도(면적 변화까지 포함)

    w, h를 쓰지 않고 s, r 사용하는 이유는
    객체의 scale variation을 안정적으로 추적 가능해서
    """

    count: int = 0

    def __init__(self, bbox_xyxy: BBox) -> None:
        KalmanBoxTracker.count += 1
        self.id: int = KalmanBoxTracker.count

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

        # 칼만 필터 기본 행렬들
        # P(초기 불확실성), Q(프로세스 노이즈), R(측정 노이즈)
        #   -> 트래킹 안정성/민감도에 큰 영향
        # 현재 값은 단순한 기본값
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

        self._ensure_x_colvec()

    def _ensure_x_colvec(self) -> None:
        # numpy 연산/브로드캐스팅으로 state 벡터 shape이 (7,)일 때,
        # 행렬 곱이 깨질 수 있어 항상 (7,1) 컬럼 벡터로 강제한다.
        self.x = np.asarray(self.x, dtype=np.float32)
        if self.x.shape == (7,):
            self.x = self.x.reshape(7, 1)
        elif self.x.ndim == 2 and self.x.shape[0] == 7 and self.x.shape[1] != 1:
            self.x = self.x[:, :1]
        elif self.x.shape != (7, 1):
            self.x = self.x.reshape(7, 1)

    def predict(self) -> BBox:
        self._ensure_x_colvec()
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        self.age += 1
        self.time_since_update += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self._ensure_x_colvec()
        return self.get_state_bbox()

    def update(self, bbox_xyxy: BBox) -> None:
        self._ensure_x_colvec()

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
        inv = np.linalg.inv(S + 1e-9 * np.eye(4, dtype=np.float32))
        K = self.P @ self.H.T @ inv

        self.x = self.x + (K @ y)
        identity = np.eye(7, dtype=np.float32)
        self.P = (identity - K @ self.H) @ self.P

        self._ensure_x_colvec()

        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1

    def get_state_bbox(self) -> BBox:
        self._ensure_x_colvec()
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


class SortTracker:
    def __init__(self, cfg: TrackConfig) -> None:
        self.cfg = cfg
        self.trackers: list[KalmanBoxTracker] = []
        self.frame_count: int = 0

    def update(self, dets_xyxy: list[BBox]) -> list[Track]:
        """
        한 프레임의 detection(bbox list)을 받아 SORT 트랙을 갱신, (x1,y1,x2,y2,id) 반환

        cfg 의미
        - iou_threshold: detection<->prediction 매칭 최소 IoU(엄격할수록 ID 유지 보수적)
        - max_age: 업데이트 못 받은 트랙을 몇 프레임까지 유지할지(가림/미검출 대비)
        - min_hits: 트랙 확정까지 필요한 히트 수(초기 오탐 억제 <-> 초기 지연)
        """
        self.frame_count += 1
        preds = [trk.predict() for trk in self.trackers]
        matched, unmatched_dets, _unmatched_trks = self._associate(dets_xyxy, preds)

        for det_idx, trk_idx in matched:
            self.trackers[trk_idx].update(dets_xyxy[det_idx])

        for i in unmatched_dets:
            self.trackers.append(KalmanBoxTracker(dets_xyxy[i]))

        self.trackers = [
            t for t in self.trackers if t.time_since_update <= self.cfg.max_age
        ]

        # min_hits를 만족한 트랙만 출력하여 초기 1~2프레임 오탐 감소
        # 단, 초기 프레임에서는 트랙이 아직 충분하지 않아 frame_count로 예외 처리
        outputs: list[Track] = []
        for trk in self.trackers:
            if trk.hits >= self.cfg.min_hits or self.frame_count <= self.cfg.min_hits:
                b = trk.get_state_bbox()
                outputs.append((b[0], b[1], b[2], b[3], trk.id))
        return outputs

    def _associate(
        self,
        dets: list[BBox],
        preds: list[BBox],
    ) -> tuple[list[tuple[int, int]], list[int], list[int]]:
        # IoU matrix: det(row) <-> pred(col)
        # - Hungarian: 비용(1-IoU) 최소화로 전역 최적 매칭
        # - Greedy: IoU 큰 순서대로 매칭(근사)
        # iou_threshold 미만은 매칭 불가로 처리해 잘못된 연결 줄임.
        if len(preds) == 0:
            return [], list(range(len(dets))), []
        if len(dets) == 0:
            return [], [], list(range(len(preds)))

        iou_mat = np.zeros((len(dets), len(preds)), dtype=np.float32)
        for d, det in enumerate(dets):
            for t, pr in enumerate(preds):
                iou_mat[d, t] = iou_xyxy(det, pr)

        matched: list[tuple[int, int]] = []
        unmatched_dets = list(range(len(dets)))
        unmatched_trks = list(range(len(preds)))

        if SCIPY_OK:
            cost = 1.0 - iou_mat
            r, c = linear_sum_assignment(cost)
            for rr, cc in zip(r, c, strict=False):
                if iou_mat[rr, cc] >= self.cfg.iou_threshold:
                    matched.append((rr, cc))
            matched_dets = {m[0] for m in matched}
            matched_trks = {m[1] for m in matched}
            unmatched_dets = [i for i in range(len(dets)) if i not in matched_dets]
            unmatched_trks = [i for i in range(len(preds)) if i not in matched_trks]
        else:
            pairs = [
                (float(iou_mat[d, t]), d, t)
                for d in range(len(dets))
                for t in range(len(preds))
            ]
            pairs.sort(reverse=True, key=lambda x: x[0])
            used_d: set[int] = set()
            used_t: set[int] = set()
            for iouv, d, t in pairs:
                if iouv < self.cfg.iou_threshold:
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
        self.trackers = []
        self.frame_count = 0
