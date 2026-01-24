from __future__ import annotations

import os

from app.rtn.audio.ffmpeg import FFmpegAudioExtractor
from app.rtn.audio.vad_silero import SileroVAD
from app.rtn.config import VADConfig


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


def vad_segments_from_video(
    video_path: str,
    vad: SileroVAD,
    cfg: VADConfig,
    tmp_dir: str,
) -> list[tuple[float, float]]:
    os.makedirs(tmp_dir, exist_ok=True)
    wav_path = os.path.join(tmp_dir, "audio_16k_mono.wav")
    FFmpegAudioExtractor.extract_wav(video_path, wav_path, sr=cfg.sr)
    segs = vad.segments_from_wav(wav_path)
    return merge_close_segments(segs, gap_s=cfg.merge_gap_s)
