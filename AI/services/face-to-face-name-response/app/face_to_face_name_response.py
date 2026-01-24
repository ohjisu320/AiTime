import logging
import math
import os
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
import numpy.typing as npt

from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    FaceDetConfig,
    GazeSmoothConfig,
    ROIConfig,
    RoleAssignConfig,
    TrackConfig,
    VADConfig,
)
from app.rtn.types import BBox, FrameBGR, Landmarks, MaskU8, Track

# scipy는 SORT 매칭(헝가리안)에 쓰고, 없으면 greedy fallback
try:
    from scipy.optimize import linear_sum_assignment

    SCIPY_OK = True
except Exception:
    SCIPY_OK = False

# -----------------------------
# Logging
# -----------------------------
logger = logging.getLogger("RTNAnalyzer")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


# -----------------------------
# Utils
# -----------------------------
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


def contact_by_raycast(
    eye_mask: MaskU8,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    n_samples: int = 11,
) -> bool:
    h, w = eye_mask.shape[:2]
    sx, sy = start_xy
    ex, ey = end_xy
    for i in range(n_samples):
        t = i / (n_samples - 1)
        x = int(clamp(sx + (ex - sx) * t, 0, w - 1))
        y = int(clamp(sy + (ey - sy) * t, 0, h - 1))
        if eye_mask[y, x] > 0:
            return True
    return False


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


# -----------------------------
# Audio extraction / VAD
# -----------------------------
class FFmpegAudioExtractor:
    @staticmethod
    def extract_wav(video_path: str, wav_path: str, sr: int = 16000) -> None:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(sr),
            "-f",
            "wav",
            wav_path,
        ]
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if p.returncode != 0:
            raise RuntimeError(f"ffmpeg 실패:\n{p.stderr}")


class SileroVAD:
    """
    torch.hub 기반 Silero VAD 래퍼.
    - 최초 1회 모델 다운로드 필요할 수 있음
    """

    _loaded: bool = False
    _model: Any | None = None
    _get_speech_timestamps: Callable[..., Any] | None = None

    def __init__(self, cfg: VADConfig) -> None:
        self.cfg = cfg
        self._ensure_loaded()

    @classmethod
    def _ensure_loaded(cls) -> None:
        if cls._loaded:
            return

        import torch  # noqa: PLC0415

        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        (
            get_speech_timestamps,
            _save_audio,
            _read_audio,
            _VADIterator,
            _collect_chunks,
        ) = utils

        cls._model = model
        cls._get_speech_timestamps = staticmethod(get_speech_timestamps)
        cls._loaded = True

    def segments_from_video(
        self, video_path: str, tmp_dir: str
    ) -> list[tuple[float, float]]:
        os.makedirs(tmp_dir, exist_ok=True)
        wav_path = os.path.join(tmp_dir, "audio_16k_mono.wav")
        FFmpegAudioExtractor.extract_wav(video_path, wav_path, sr=self.cfg.sr)
        return self.segments_from_wav(wav_path)

    def segments_from_wav(self, wav_path: str) -> list[tuple[float, float]]:
        import soundfile as sf  # noqa: PLC0415
        import torch  # noqa: PLC0415

        audio, file_sr = sf.read(wav_path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if file_sr != self.cfg.sr:
            raise RuntimeError(
                f"WAV sample rate mismatch: expected {self.cfg.sr}, got {file_sr}",
            )

        wav = torch.from_numpy(audio).float()

        if self._get_speech_timestamps is None or self._model is None:
            raise RuntimeError("SileroVAD not initialized properly.")

        ts = self._get_speech_timestamps(
            wav,
            self._model,
            sampling_rate=self.cfg.sr,
            min_speech_duration_ms=self.cfg.min_speech_ms,
            min_silence_duration_ms=self.cfg.min_silence_ms,
            return_seconds=False,
        )

        segs = [(t["start"] / self.cfg.sr, t["end"] / self.cfg.sr) for t in ts]
        return [(float(s), float(e)) for s, e in segs]


def merge_close_segments(
    segs: list[tuple[float, float]],
    gap_s: float,
) -> list[tuple[float, float]]:
    if not segs:
        return []
    segs = sorted(segs, key=lambda x: x[0])
    merged = [segs[0]]
    for s, e in segs[1:]:
        ps, pe = merged[-1]
        if s - pe <= gap_s:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


# -----------------------------
# SORT (minimal)
# -----------------------------
class KalmanBoxTracker:
    """
    state: [cx, cy, s, r, vx, vy, vs]^T
    where s=area, r=aspect ratio
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

    def update(
        self, dets_xyxy: list[BBox]
    ) -> list[tuple[float, float, float, float, int]]:
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

        outputs: list[tuple[float, float, float, float, int]] = []
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


# -----------------------------
# MediaPipe wrappers
# -----------------------------
class FaceDetectorMP:
    def __init__(self, cfg: FaceDetConfig) -> None:
        # mediapipe 자체가 특정 파이썬 버전에서 깨질 수 있어(특히 최신버전)
        if not hasattr(mp, "solutions"):
            raise RuntimeError(
                "mediapipe에 solutions가 없습니다. "
                "(파이썬/mediapipe 호환성 문제 가능)\n"
                "권장: Python 3.10~3.12 + 안정 mediapipe",
            )
        self.cfg = cfg
        self.mp_fd = mp.solutions.face_detection
        self.detector = self.mp_fd.FaceDetection(
            model_selection=cfg.model_selection,
            min_detection_confidence=cfg.min_conf,
        )

    def detect(
        self, frame_bgr: FrameBGR
    ) -> list[tuple[float, float, float, float, float]]:
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.detector.process(rgb)
        out: list[tuple[float, float, float, float, float]] = []
        if not res.detections:
            return out
        for det in res.detections:
            score = float(det.score[0]) if det.score else 0.0
            b = det.location_data.relative_bounding_box
            x1 = b.xmin * w
            y1 = b.ymin * h
            x2 = (b.xmin + b.width) * w
            y2 = (b.ymin + b.height) * h
            out.append((x1, y1, x2, y2, score))
        return out


class FaceMeshMP:
    """
    - trk_mesh: 빠른 tracking 모드 (static_image_mode=False)
    - det_mesh: 초기 검출/복구용 (static_image_mode=True)
    """

    def __init__(
        self,
        refine_landmarks: bool = True,
        det_min_conf: float = 0.3,  # 초기/측면은 낮추는 게 유리
        trk_min_conf: float = 0.5,
        trk_min_track: float = 0.5,
        min_crop_size: int = 160,  # 너무 작으면 업스케일
        upscale_to: int = 256,
    ) -> None:
        self.min_crop_size = int(min_crop_size)
        self.upscale_to = int(upscale_to)

        self.trk_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=trk_min_conf,
            min_tracking_confidence=trk_min_track,
        )

        self.det_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=det_min_conf,
            min_tracking_confidence=0.0,
        )

    def _run(self, mesh: Any, face_bgr: FrameBGR) -> Landmarks | None:
        h, w = face_bgr.shape[:2]
        if h < 2 or w < 2:
            return None

        # 작은 crop은 초기 검출이 특히 약함 → 업스케일
        scale_x = 1.0
        scale_y = 1.0
        img = face_bgr

        if min(h, w) < self.min_crop_size:
            target = self.upscale_to
            img = cv2.resize(
                face_bgr,
                (target, target),
                interpolation=cv2.INTER_LINEAR,
            )
            scale_x = w / target
            scale_y = h / target
            h2, w2 = img.shape[:2]
        else:
            h2, w2 = h, w

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = mesh.process(rgb)
        if not res.multi_face_landmarks:
            return None

        lm = res.multi_face_landmarks[0].landmark
        pts: Landmarks = []
        for p in lm:
            x = p.x * w2
            y = p.y * h2
            # 원래 crop 좌표로 되돌리기
            x *= scale_x
            y *= scale_y
            pts.append((x, y, p.z))
        return pts

    def landmarks(self, face_bgr: FrameBGR) -> Landmarks | None:
        # 1) tracking mesh 우선
        pts = self._run(self.trk_mesh, face_bgr)
        if pts is not None:
            return pts
        # 2) 실패하면 detection mesh로 “초기 잡기”
        return self._run(self.det_mesh, face_bgr)


# -----------------------------
# FaceMesh indices
# -----------------------------
LEFT_EYE_CONTOUR = [
    33,
    7,
    163,
    144,
    145,
    153,
    154,
    155,
    133,
    173,
    157,
    158,
    159,
    160,
    161,
    246,
]
RIGHT_EYE_CONTOUR = [
    362,
    382,
    381,
    380,
    374,
    373,
    390,
    249,
    263,
    466,
    388,
    387,
    386,
    385,
    384,
    398,
]

LEFT_EYE_OUTER = 33
RIGHT_EYE_OUTER = 263

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]


# -----------------------------
# Gaze / ROI
# -----------------------------
def iris_center(pts: Landmarks, iris_indices: Sequence[int]) -> tuple[float, float]:
    xs = [pts[i][0] for i in iris_indices]
    ys = [pts[i][1] for i in iris_indices]
    return float(np.mean(xs)), float(np.mean(ys))


def eye_ratio(pts: Landmarks) -> tuple[float, float]:
    def one_eye(
        iris_idx: Sequence[int],
        contour_idx: Sequence[int],
    ) -> tuple[float, float, float]:
        cx, cy = iris_center(pts, iris_idx)
        eye = np.array(
            [[pts[i][0], pts[i][1]] for i in contour_idx],
            dtype=np.float32,
        )
        x0, x1 = float(eye[:, 0].min()), float(eye[:, 0].max())
        y0, y1 = float(eye[:, 1].min()), float(eye[:, 1].max())
        xr = (cx - x0) / ((x1 - x0) + 1e-6)
        yr = (cy - y0) / ((y1 - y0) + 1e-6)
        q = (x1 - x0) * (y1 - y0)
        return float(xr), float(yr), float(q)

    lxr, lyr, lq = one_eye(LEFT_IRIS, LEFT_EYE_CONTOUR)
    rxr, ryr, rq = one_eye(RIGHT_IRIS, RIGHT_EYE_CONTOUR)

    qsum = lq + rq
    if qsum > 1e-6:
        wl = lq / qsum
        wr = rq / qsum
        xr = wl * lxr + wr * rxr
        yr = wl * lyr + wr * ryr
    else:
        xr = (lxr + rxr) / 2.0
        yr = (lyr + ryr) / 2.0

    dx = xr - 0.5
    dy = yr - 0.5
    return dx, dy


def gaze_vector_end(
    start_xy: tuple[float, float],
    dx: float,
    dy: float,
    img_w: int,
    img_h: int,
    scale: float = 2.0,
) -> tuple[float, float]:
    sx, sy = start_xy
    vx = dx * img_w * scale
    vy = dy * img_h * scale
    return (float(sx + vx), float(sy + vy))


class GazeEstimatorIrisRatio:
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
        dx, dy = eye_ratio(clm)

        if abs(dx) < self.cfg.deadzone:
            dx = 0.0
        if abs(dy) < self.cfg.deadzone:
            dy = 0.0

        if not self._has:
            self._dx_f, self._dy_f = dx, dy
            self._has = True
        else:
            dx = self._dx_f + float(
                np.clip(dx - self._dx_f, -self.cfg.max_jump, +self.cfg.max_jump),
            )
            dy = self._dy_f + float(
                np.clip(dy - self._dy_f, -self.cfg.max_jump, +self.cfg.max_jump),
            )
            self._dx_f = self.cfg.alpha * dx + (1 - self.cfg.alpha) * self._dx_f
            self._dy_f = self.cfg.alpha * dy + (1 - self.cfg.alpha) * self._dy_f

        dx, dy = self._dx_f, self._dy_f
        end_raw = gaze_vector_end(
            start_xy,
            dx,
            dy,
            img_w=img_w,
            img_h=img_h,
            scale=self.cfg.gaze_scale,
        )

        end_smoothed = smooth_xy(
            self._end_f,
            end_raw,
            alpha=self.cfg.end_alpha,
            max_jump=self.cfg.end_jump_px,
        )
        self._end_f = end_smoothed
        return end_smoothed, dx, dy


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
            [[plm[i][0] + ox, plm[i][1] + oy] for i in idxs],
            dtype=np.float32,
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
            [[rx1, ry1], [rx2, ry1], [rx2, ry2], [rx1, ry2]],
            dtype=np.int32,
        )
        return rect, mask, "bbox_fallback"


# -----------------------------
# Debug Renderer
# -----------------------------
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
        delay_ms = max(1, int(1000.0 / fps))
        cv2.imshow("debug", dbg)
        return (cv2.waitKey(delay_ms) & 0xFF) == 27


# -----------------------------
# Roles
# -----------------------------
class RoleAssignerByArea:
    """
    warmup 구간에서 track별 평균 얼굴 면적을 누적해,
    큰 얼굴 = parent, 작은 얼굴 = child 로 지정
    """

    def __init__(self, warmup_s: float) -> None:
        self.warmup_s = warmup_s
        self.stats: dict[int, dict[str, float]] = {}
        self.assigned: bool = False
        self.parent_id: int | None = None
        self.child_id: int | None = None

    def update_warmup(
        self,
        cur_t: float,
        start_t: float,
        tracks: list[Track],
    ) -> None:
        if cur_t <= start_t + self.warmup_s:
            for x1, y1, x2, y2, tid in tracks:
                area = bbox_area_xyxy((x1, y1, x2, y2))
                st = self.stats.setdefault(tid, {"sum_area": 0.0, "cnt": 0.0})
                st["sum_area"] += area
                st["cnt"] += 1.0

    def maybe_assign(self, cur_t: float, start_t: float) -> None:
        if self.assigned:
            return
        if cur_t < start_t + self.warmup_s:
            return
        if len(self.stats) < 2:
            return

        items: list[tuple[float, float, int]] = []
        for tid, st in self.stats.items():
            if st["cnt"] <= 0:
                continue
            mean_area = st["sum_area"] / st["cnt"]
            items.append((st["cnt"], mean_area, tid))
        items.sort(reverse=True)

        top2 = items[:2]
        if len(top2) != 2:
            return

        if top2[0][1] >= top2[1][1]:
            self.parent_id = top2[0][2]
            self.child_id = top2[1][2]
        else:
            self.parent_id = top2[1][2]
            self.child_id = top2[0][2]

        self.assigned = True


# -----------------------------
# Results
# -----------------------------
@dataclass
class CallResult:
    call_index: int
    call_start: float
    call_end: float
    success: bool
    latency_s: float | None
    gaze_duration_s: float


# -----------------------------
# Window Analyzer
# -----------------------------
class WindowAnalyzer:
    def __init__(
        self,
        detector: FaceDetectorMP,
        facemesh: FaceMeshMP,
        track_cfg: TrackConfig,
        role_cfg: RoleAssignConfig,
        roi_cfg: ROIConfig,
        gaze_cfg: GazeSmoothConfig,
        contact_cfg: ContactConfig,
        analysis_cfg: AnalysisConfig,
        conf_th: float,
        debug_publish: Callable[[FrameBGR], None] | None = None,
    ) -> None:
        self.detector = detector
        self.facemesh = facemesh
        self.tracker = SortTracker(track_cfg)
        self.role_cfg = role_cfg
        self.roi_builder = ParentEyeROIBuilder(roi_cfg)
        self.gaze_estimator = GazeEstimatorIrisRatio(gaze_cfg)
        self.contact_cfg = contact_cfg
        self.analysis_cfg = analysis_cfg
        self.conf_th = conf_th
        self.debug_publish = debug_publish

    def analyze_call(
        self,
        video_path: str,
        call_idx: int,
        call_start: float,
        call_end: float,
    ) -> CallResult:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"비디오 열기 실패: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if self.analysis_cfg.fps_override and self.analysis_cfg.fps_override > 0:
            fps = self.analysis_cfg.fps_override
        fps = fps if fps and fps > 1e-3 else 30.0
        dt = 1.0 / fps

        start_t = max(0.0, call_end)
        end_t = call_end + self.analysis_cfg.window_s
        cap.set(cv2.CAP_PROP_POS_MSEC, start_t * 1000.0)

        role_assigner = RoleAssignerByArea(self.role_cfg.warmup_s)

        consec_contact: int = 0
        first_contact_time: float | None = None
        gaze_duration: float = 0.0

        debug = DebugRenderer(self.analysis_cfg.debug)
        frame_idx: int = 0

        # debug 창 OR MJPEG publish 둘 중 하나라도 켜져있으면 dbg 프레임을 만든다
        debug_mode = self.analysis_cfg.debug or (self.debug_publish is not None)

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                frame_idx += 1
                cur_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                cur_t = cur_msec / 1000.0
                if cur_t > end_t:
                    break

                h, w = frame.shape[:2]
                dbg: FrameBGR | None = frame.copy() if debug_mode else None

                # detect + track
                dets = self.detector.detect(frame)
                dets = [d for d in dets if d[4] >= self.conf_th]
                dets_xyxy: list[BBox] = [(d[0], d[1], d[2], d[3]) for d in dets]
                tracks = self.tracker.update(dets_xyxy)

                role_assigner.update_warmup(cur_t, start_t, tracks)
                role_assigner.maybe_assign(cur_t, start_t)

                if debug_mode and dbg is not None:
                    msg = (
                        f"t={cur_t:.2f}s tracks={len(tracks)} "
                        f"role={role_assigner.assigned}"
                    )
                    cv2.putText(
                        dbg,
                        msg,
                        (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2,
                    )
                    for x1, y1, x2, y2, tid in tracks:
                        cv2.rectangle(
                            dbg,
                            (int(x1), int(y1)),
                            (int(x2), int(y2)),
                            (200, 200, 0),
                            2,
                        )
                        cv2.putText(
                            dbg,
                            f"id={tid}",
                            (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (200, 200, 0),
                            2,
                        )

                # role 미할당: 계속 publish 해야 /debug/mjpeg가 무한로딩 안 함
                if not role_assigner.assigned:
                    if debug_mode and dbg is not None:
                        cv2.putText(
                            dbg,
                            "role not assigned",
                            (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )

                    if self.debug_publish is not None and dbg is not None:
                        self.debug_publish(dbg)

                    if (
                        self.analysis_cfg.debug
                        and dbg is not None
                        and debug.show(dbg, fps)
                    ):
                        break
                    continue

                parent_id = role_assigner.parent_id
                child_id = role_assigner.child_id
                if parent_id is None or child_id is None:
                    continue

                # locate bboxes
                parent_bbox: BBox | None = None
                child_bbox: BBox | None = None
                for x1, y1, x2, y2, tid in tracks:
                    if tid == parent_id:
                        parent_bbox = (x1, y1, x2, y2)
                    elif tid == child_id:
                        child_bbox = (x1, y1, x2, y2)

                # tracking lost도 publish
                if parent_bbox is None or child_bbox is None:
                    consec_contact = 0

                    if debug_mode and dbg is not None:
                        cv2.putText(
                            dbg,
                            "tracking lost",
                            (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )

                    if self.debug_publish is not None and dbg is not None:
                        self.debug_publish(dbg)

                    if (
                        self.analysis_cfg.debug
                        and dbg is not None
                        and debug.show(dbg, fps)
                    ):
                        break
                    continue

                # crop
                parent_crop, (pox, poy) = crop_face_square(
                    frame, parent_bbox, margin=0.25
                )
                child_crop, (cox, coy) = crop_face_square(
                    frame, child_bbox, margin=0.40
                )

                # facemesh
                plm = self.facemesh.landmarks(parent_crop)  # optional
                clm = self.facemesh.landmarks(child_crop)  # required
                if clm is None:
                    consec_contact = 0

                    if debug_mode and dbg is not None:
                        cv2.putText(
                            dbg,
                            "child facemesh failed",
                            (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )

                    if self.debug_publish is not None and dbg is not None:
                        self.debug_publish(dbg)

                    if (
                        self.analysis_cfg.debug
                        and dbg is not None
                        and debug.show(dbg, fps)
                    ):
                        break
                    continue

                # child gaze start point: outer corners mid
                cleft_outer = (
                    clm[LEFT_EYE_OUTER][0] + cox,
                    clm[LEFT_EYE_OUTER][1] + coy,
                )
                cright_outer = (
                    clm[RIGHT_EYE_OUTER][0] + cox,
                    clm[RIGHT_EYE_OUTER][1] + coy,
                )
                sx = (cleft_outer[0] + cright_outer[0]) / 2.0
                sy = (cleft_outer[1] + cright_outer[1]) / 2.0

                end_pt, dx, dy = self.gaze_estimator.estimate_end_point(
                    clm,
                    (sx, sy),
                    img_w=w,
                    img_h=h,
                )

                # parent ROI
                if plm is not None:
                    hull, eye_mask, roi_mode = self.roi_builder.from_mesh(
                        plm,
                        (pox, poy),
                        img_h=h,
                        img_w=w,
                    )
                else:
                    hull, eye_mask, roi_mode = self.roi_builder.from_bbox_fallback(
                        parent_bbox,
                        img_h=h,
                        img_w=w,
                    )

                contact = contact_by_raycast(
                    eye_mask,
                    (sx, sy),
                    end_pt,
                    n_samples=self.contact_cfg.raycast_samples,
                )

                if contact:
                    consec_contact += 1
                    gaze_duration += dt
                    if (
                        first_contact_time is None
                        and consec_contact >= self.contact_cfg.min_contact_frames
                    ):
                        first_contact_time = cur_t
                    status_msg = f"CONTACT ({roi_mode})"
                    status_color = (0, 255, 0)
                else:
                    consec_contact = 0
                    status_msg = f"no contact ({roi_mode})"
                    status_color = (0, 255, 255)

                # debug overlay는 debug_mode 기준으로 (스트리밍에도 뜨게)
                if debug_mode and dbg is not None:
                    px1, py1, px2, py2 = map(int, parent_bbox)
                    cx1, cy1, cx2, cy2 = map(int, child_bbox)

                    cv2.rectangle(dbg, (px1, py1), (px2, py2), (255, 255, 0), 2)
                    cv2.putText(
                        dbg,
                        "P",
                        (px1, py1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (255, 255, 0),
                        2,
                    )

                    cv2.rectangle(dbg, (cx1, cy1), (cx2, cy2), (0, 255, 255), 2)
                    cv2.putText(
                        dbg,
                        "C",
                        (cx1, cy1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 255, 255),
                        2,
                    )

                    overlay = dbg.copy()
                    overlay[eye_mask > 0] = (0, 255, 0)
                    dbg = cv2.addWeighted(overlay, 0.25, dbg, 0.75, 0)

                    cv2.polylines(dbg, [hull], True, (0, 255, 0), 2)

                    DebugRenderer.draw_indices(
                        dbg,
                        clm,
                        LEFT_IRIS,
                        offset=(cox, coy),
                        color=(255, 0, 255),
                        radius=2,
                    )
                    DebugRenderer.draw_indices(
                        dbg,
                        clm,
                        RIGHT_IRIS,
                        offset=(cox, coy),
                        color=(255, 0, 255),
                        radius=2,
                    )

                    cv2.circle(dbg, (int(sx), int(sy)), 3, (255, 0, 0), -1)
                    cv2.circle(
                        dbg,
                        (int(end_pt[0]), int(end_pt[1])),
                        5,
                        (0, 0, 255),
                        -1,
                    )
                    cv2.line(
                        dbg,
                        (int(sx), int(sy)),
                        (int(end_pt[0]), int(end_pt[1])),
                        (0, 0, 255),
                        2,
                    )

                    status_line = (
                        f"{status_msg} consec={consec_contact} "
                        f"dx={dx:+.3f} dy={dy:+.3f}"
                    )
                    cv2.putText(
                        dbg,
                        status_line,
                        (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        status_color,
                        2,
                    )

                # 매 프레임 publish (가장 중요)
                if self.debug_publish is not None and dbg is not None:
                    self.debug_publish(dbg)

                # 로컬 GUI debug 창은 debug=True일 때만
                if self.analysis_cfg.debug and dbg is not None and debug.show(dbg, fps):
                    break

        finally:
            cap.release()
            debug.close()

        success = first_contact_time is not None
        latency = (first_contact_time - call_end) if success else None

        return CallResult(
            call_index=call_idx,
            call_start=call_start,
            call_end=call_end,
            success=success,
            latency_s=latency,
            gaze_duration_s=float(gaze_duration),
        )

    def _publish_dbg(self, dbg: FrameBGR | None) -> None:
        if self.debug_publish is not None and dbg is not None:
            self.debug_publish(dbg)


# -----------------------------
# Video Analyzer (orchestration)
# -----------------------------
class VideoAnalyzer:
    def __init__(
        self,
        vad_cfg: VADConfig,
        face_cfg: FaceDetConfig,
        track_cfg: TrackConfig,
        role_cfg: RoleAssignConfig,
        roi_cfg: ROIConfig,
        gaze_cfg: GazeSmoothConfig,
        contact_cfg: ContactConfig,
        analysis_cfg: AnalysisConfig,
        conf_th: float,
    ) -> None:
        self.vad_cfg = vad_cfg
        self.analysis_cfg = analysis_cfg

        self.vad = SileroVAD(vad_cfg)
        self.detector = FaceDetectorMP(face_cfg)
        self.facemesh = FaceMeshMP()

        self.window_analyzer = WindowAnalyzer(
            detector=self.detector,
            facemesh=self.facemesh,
            track_cfg=track_cfg,
            role_cfg=role_cfg,
            roi_cfg=roi_cfg,
            gaze_cfg=gaze_cfg,
            contact_cfg=contact_cfg,
            analysis_cfg=analysis_cfg,
            conf_th=conf_th,
        )

    def analyze(self, video_path: str) -> dict[str, Any]:
        tmp_dir = os.path.join(
            os.path.dirname(os.path.abspath(video_path)),
            self.vad_cfg.tmp_dirname,
        )

        segs = self.vad.segments_from_video(video_path, tmp_dir=tmp_dir)
        segs = merge_close_segments(segs, gap_s=self.vad_cfg.merge_gap_s)

        logger.info("VAD segs: %d (show first 5) %s", len(segs), segs[:5])

        results: list[CallResult] = []
        for i, (s, e) in enumerate(segs, start=1):
            r = self.window_analyzer.analyze_call(
                video_path,
                call_idx=i,
                call_start=s,
                call_end=e,
            )
            results.append(r)

        total_calls = len(results)
        success_calls = sum(1 for r in results if r.success)
        total_gaze = sum(r.gaze_duration_s for r in results)
        latencies = [r.latency_s for r in results if r.latency_s is not None]
        avg_latency = float(np.mean(latencies)) if latencies else None

        params = {
            "window_s": self.analysis_cfg.window_s,
            "vad_merge_gap_s": self.vad_cfg.merge_gap_s,
            "vad_min_speech_ms": self.vad_cfg.min_speech_ms,
            "vad_min_silence_ms": self.vad_cfg.min_silence_ms,
            "min_contact_frames": self.window_analyzer.contact_cfg.min_contact_frames,
            "warmup_s": self.window_analyzer.role_cfg.warmup_s,
            "face_det_conf_th": self.window_analyzer.conf_th,
        }

        return {
            "video": os.path.basename(video_path),
            "params": params,
            "summary": {
                "success_count": int(success_calls),
                "total_call_count": int(total_calls),
                "avg_latency_s": avg_latency,
                "total_gaze_duration_s": float(total_gaze),
            },
            "per_call": [
                {
                    "call_index": r.call_index,
                    "call_start_s": r.call_start,
                    "call_end_s": r.call_end,
                    "success": r.success,
                    "latency_s": r.latency_s,
                    "gaze_duration_s": r.gaze_duration_s,
                }
                for r in results
            ],
        }


# -----------------------------
# Service helper (FastAPI용)
# -----------------------------
def build_analyzer(
    window_s: float = 5.0,
    vad_merge_gap: float = 0.3,
    vad_min_speech_ms: int = 250,
    vad_min_silence_ms: int = 250,
    min_contact_frames: int = 3,
    warmup_s: float = 1.0,
    conf: float = 0.6,
    debug: bool = False,
    fps_override: float | None = None,
) -> VideoAnalyzer:
    vad_cfg = VADConfig(
        sr=16000,
        min_speech_ms=vad_min_speech_ms,
        min_silence_ms=vad_min_silence_ms,
        merge_gap_s=vad_merge_gap,
    )
    face_cfg = FaceDetConfig(min_conf=conf, model_selection=0)
    track_cfg = TrackConfig(max_age=8, min_hits=2, iou_threshold=0.3)
    role_cfg = RoleAssignConfig(warmup_s=warmup_s)
    roi_cfg = ROIConfig(mesh_dilate_px=14, bbox_fallback_dilate_px=28)
    gaze_cfg = GazeSmoothConfig()
    contact_cfg = ContactConfig(
        min_contact_frames=min_contact_frames,
        raycast_samples=11,
    )
    analysis_cfg = AnalysisConfig(
        window_s=window_s,
        debug=debug,
        fps_override=fps_override,
    )

    return VideoAnalyzer(
        vad_cfg=vad_cfg,
        face_cfg=face_cfg,
        track_cfg=track_cfg,
        role_cfg=role_cfg,
        roi_cfg=roi_cfg,
        gaze_cfg=gaze_cfg,
        contact_cfg=contact_cfg,
        analysis_cfg=analysis_cfg,
        conf_th=conf,
    )


def analyze_video(video_path: str, analyzer: VideoAnalyzer) -> dict[str, Any]:
    t0 = time.time()
    out = analyzer.analyze(video_path)
    out["elapsed_s"] = float(time.time() - t0)
    return out
