"""
발화 모방 유사도 계산 (MFCC + DTW)

목표:
- "비슷한 소리면 OK" 판정을 위해 텍스트(STT) 없이도 비교 가능한
  오디오 기반 유사도 점수를 제공합니다.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    similarity: float  # 0~1 (높을수록 유사)
    dtw_cost: float  # 정규화 DTW 비용 (낮을수록 유사)
    used_frames_a: int
    used_frames_b: int


class AudioSimilarityDTW:
    """
    MFCC 시퀀스 간 DTW 비용을 유사도로 변환.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def score(self, a: np.ndarray, b: np.ndarray, sample_rate: int) -> SimilarityResult:
        """
        Args:
            a, b: float32 mono audio [-1,1]
        """
        mfcc_a = self._mfcc(a, sample_rate)
        mfcc_b = self._mfcc(b, sample_rate)

        if mfcc_a.size == 0 or mfcc_b.size == 0:
            return SimilarityResult(
                similarity=0.0, dtw_cost=float("inf"), used_frames_a=0, used_frames_b=0
            )

        cost = self._dtw_cost(mfcc_a, mfcc_b, radius=int(self._settings.DTW_RADIUS))
        # cost → similarity 변환 (monotonic)
        sim = 1.0 / (1.0 + cost)
        sim = float(max(0.0, min(1.0, sim)))
        return SimilarityResult(
            similarity=sim,
            dtw_cost=float(cost),
            used_frames_a=mfcc_a.shape[0],
            used_frames_b=mfcc_b.shape[0],
        )

    def _mfcc(self, y: np.ndarray, sr: int) -> np.ndarray:
        y = np.asarray(y, dtype=np.float32)
        if y.ndim != 1:
            y = y.reshape(-1)
        if len(y) < int(0.05 * sr):  # 너무 짧으면 제외
            return np.zeros((0, self._settings.N_MFCC), dtype=np.float32)

        # pre-emphasis (약하게)
        y = np.append(y[0], y[1:] - 0.97 * y[:-1])

        win = int(sr * (self._settings.WIN_LENGTH_MS / 1000.0))
        hop = int(sr * (self._settings.HOP_LENGTH_MS / 1000.0))
        win = max(256, win)
        hop = max(80, hop)

        try:
            import librosa  # type: ignore

            mfcc = librosa.feature.mfcc(
                y=y.astype(float),
                sr=sr,
                n_mfcc=int(self._settings.N_MFCC),
                n_mels=int(self._settings.N_MELS),
                n_fft=win,
                hop_length=hop,
            )
            feat = mfcc.T.astype(np.float32)  # (frames, n_mfcc)
            return self._norm(feat)
        except Exception:
            # fallback: 간단 MFCC 구현 (log-mel + DCT)
            feat = _mfcc_fallback(
                y,
                sr,
                n_mfcc=int(self._settings.N_MFCC),
                n_mels=int(self._settings.N_MELS),
                n_fft=win,
                hop=hop,
            )
            return self._norm(feat)

    @staticmethod
    def _norm(x: np.ndarray) -> np.ndarray:
        # CMVN (per-dim)
        mu = np.mean(x, axis=0, keepdims=True)
        sd = np.std(x, axis=0, keepdims=True) + 1e-6
        return (x - mu) / sd

    @staticmethod
    def _dtw_cost(a: np.ndarray, b: np.ndarray, radius: int = 1) -> float:
        """
        DTW normalized cost (euclidean). radius<=1 means full DTW.
        """
        na, nb = a.shape[0], b.shape[0]
        # band window
        band = None if radius <= 1 else radius

        # initialize dp with inf
        inf = 1e15
        dp = np.full((na + 1, nb + 1), inf, dtype=np.float32)
        dp[0, 0] = 0.0

        def dist(i: int, j: int) -> float:
            d = a[i] - b[j]
            return float(np.sqrt(np.dot(d, d) + 1e-8))

        for i in range(1, na + 1):
            j_start = 1
            j_end = nb
            if band is not None:
                j_start = max(1, i - band)
                j_end = min(nb, i + band)
            for j in range(j_start, j_end + 1):
                c = dist(i - 1, j - 1)
                dp[i, j] = c + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])

        cost = float(dp[na, nb])
        # normalize by path length upper bound
        norm = float(na + nb)
        return cost / max(1.0, norm)


def _mfcc_fallback(
    y: np.ndarray,
    sr: int,
    n_mfcc: int,
    n_mels: int,
    n_fft: int,
    hop: int,
) -> np.ndarray:
    """
    아주 간단한 MFCC fallback
    - STFT power
    - mel filterbank
    - log
    - DCT-II
    """
    # framing
    win = n_fft
    if len(y) < win:
        return np.zeros((0, n_mfcc), dtype=np.float32)

    # window
    window = np.hanning(win).astype(np.float32)

    frames = []
    for i in range(0, len(y) - win + 1, hop):
        frames.append(y[i : i + win] * window)
    X = np.stack(frames, axis=0)  # (frames, win)

    # rfft
    S = np.fft.rfft(X, n=win, axis=1)
    P = (np.abs(S) ** 2).astype(np.float32)  # power
    freqs = np.fft.rfftfreq(win, d=1.0 / sr).astype(np.float32)

    # mel filterbank
    fb = _mel_filterbank(freqs, n_mels=n_mels, fmin=0.0, fmax=sr / 2)
    M = np.maximum(1e-10, P @ fb.T)  # (frames, n_mels)
    logM = np.log(M).astype(np.float32)

    # DCT-II
    dct = _dct_matrix(n_mels, n_mfcc)
    mfcc = logM @ dct.T  # (frames, n_mfcc)
    return mfcc.astype(np.float32)


def _hz_to_mel(hz: float) -> float:
    return 2595.0 * math.log10(1.0 + hz / 700.0)


def _mel_to_hz(mel: float) -> float:
    return 700.0 * (10 ** (mel / 2595.0) - 1.0)


def _mel_filterbank(
    freqs: np.ndarray, n_mels: int, fmin: float, fmax: float
) -> np.ndarray:
    mels = np.linspace(_hz_to_mel(fmin), _hz_to_mel(fmax), n_mels + 2)
    hz = np.array([_mel_to_hz(m) for m in mels], dtype=np.float32)

    fb = np.zeros((n_mels, len(freqs)), dtype=np.float32)
    for i in range(n_mels):
        f_left, f_center, f_right = hz[i], hz[i + 1], hz[i + 2]
        # triangles
        left = (freqs - f_left) / max(1e-6, (f_center - f_left))
        right = (f_right - freqs) / max(1e-6, (f_right - f_center))
        fb[i] = np.maximum(0.0, np.minimum(left, right))
    return fb


def _dct_matrix(n_in: int, n_out: int) -> np.ndarray:
    # DCT-II basis
    mat = np.zeros((n_out, n_in), dtype=np.float32)
    factor = math.pi / n_in
    for k in range(n_out):
        for n in range(n_in):
            mat[k, n] = math.cos((n + 0.5) * k * factor)
    mat[0] *= 1.0 / math.sqrt(n_in)
    if n_out > 1:
        mat[1:] *= math.sqrt(2.0 / n_in)
    return mat
