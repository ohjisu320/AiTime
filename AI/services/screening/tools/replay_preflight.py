import argparse
import contextlib
import json
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml
from src.contracts.context import ROI, PreflightConfig, RunContext, make_repro_keys
from src.pipelines.orchestrator import PreflightOrchestrator


@dataclass
class FakeClock:
    t: float = 0.0

    def now(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += float(dt)


def load_config(path: str = "configs/preflight.yaml") -> PreflightConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    cfg = PreflightConfig(
        schema_version=raw.get("schema_version", "1.0"),
        task_type=raw.get("task_type", "PREFLIGHT_SCREENING"),
        window_sec=float(raw["window_sec"]),
        max_total_time_sec=float(raw["max_total_time_sec"]),
        sample_video_fps=int(raw["sample_video_fps"]),
        target_faces=int(raw["target_faces"]),
        audio_noise_dbfs_threshold=float(raw["audio"]["noise_dbfs_threshold"]),
        audio_noise_high_ratio_max=float(raw["audio"]["noise_high_ratio_max"]),
        audio_chunk_sec=float(raw["audio"].get("chunk_sec", 0.5)),
        video_luma_mean_threshold=float(raw["video"]["luma_mean_threshold"]),
        video_low_light_ratio_max=float(raw["video"]["low_light_ratio_max"]),
        faces_two_faces_ratio_min=float(raw["faces"]["two_faces_ratio_min"]),
        faces_min_face_area_ratio=float(raw["faces"]["min_face_area_ratio"]),
        roi_face_ratio_min=float(raw["roi"]["roi_face_ratio_min"]),
        roi_1=ROI(**raw["roi"]["roi_1"]),
        roi_2=ROI(**raw["roi"]["roi_2"]),
        # decision defaults (없어도 돌아가게)
        min_video_samples=int(raw.get("decision", {}).get("min_video_samples", 10)),
        min_audio_samples=int(raw.get("decision", {}).get("min_audio_samples", 3)),
        progress_interval_sec=float(
            raw.get("decision", {}).get("progress_interval_sec", 0.3)
        ),
        hint_interval_sec=float(raw.get("decision", {}).get("hint_interval_sec", 1.0)),
        pass_hold_sec=float(raw.get("decision", {}).get("pass_hold_sec", 1.0)),
        # logs/debug는 테스트에선 기본 off
        logs_enabled=bool(raw.get("logs", {}).get("enabled", False)),
        logs_dir=str(raw.get("logs", {}).get("dir", "artifacts/preflight/logs")),
        stage_log_interval_sec=float(
            raw.get("logs", {}).get("stage_log_interval_sec", 1.0)
        ),
        debug_enabled=bool(raw.get("debug", {}).get("enabled", False)),
        debug_save_mismatch_only=bool(
            raw.get("debug", {}).get("save_mismatch_only", True)
        ),
        debug_sample_rate=float(raw.get("debug", {}).get("sample_rate", 0.2)),
        debug_save_on_flags=list(raw.get("debug", {}).get("save_on_flags", [])),
        debug_artifacts_dir=str(
            raw.get("debug", {}).get("artifacts_dir", "artifacts/preflight")
        ),
    )
    return cfg


def ffmpeg_extract_wav(mp4: Path, wav_out: Path, sr: int = 16000) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(mp4),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sr),
        "-f",
        "wav",
        str(wav_out),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {p.stdout}")


def read_wav_float32(wav_path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(wav_path), "rb") as wf:
        ch = wf.getnchannels()
        sr = wf.getframerate()
        n = wf.getnframes()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(n)

    if sampwidth != 2:
        raise ValueError("Only 16-bit PCM wav supported in this helper.")

    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        pcm = pcm.reshape(-1, ch).mean(axis=1)
    return pcm, sr


def replay(mp4_path: Path, config_path: str, config_version: str) -> dict[str, Any]:
    cfg = load_config(config_path)

    run_id = f"golden_{mp4_path.stem}"
    repro = make_repro_keys(
        run_id=run_id,
        code_sha="test",
        config_version=config_version,
        env_lock_hash="test",
    )
    ctx = RunContext(
        repro=repro,
        trace_id=run_id,
        config=cfg,
        roi_1=cfg.roi_1,
        roi_2=cfg.roi_2,
        client_info={"mode": "replay", "asset": mp4_path.name},
    )

    msgs: list[dict] = []

    def send(m: dict) -> None:
        msgs.append(m)

    clock = FakeClock(0.0)
    orch = PreflightOrchestrator(ctx, send=send, now_fn=clock.now)

    # --- video ---
    cap = cv2.VideoCapture(str(mp4_path))
    if not cap.isOpened():
        raise RuntimeError(f"failed to open video: {mp4_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1e-3:
        fps = 30.0

    # video sampling tick
    # (orchestrator가 sample_video_fps로 샘플링하므로, 여기선 그보다 약간 촘촘히)
    tick = 1.0 / max(1, int(cfg.sample_video_fps))

    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()

    duration = len(frames) / fps

    # --- audio (extract) ---
    tmp_wav = mp4_path.with_suffix(".tmp.wav")
    ffmpeg_extract_wav(mp4_path, tmp_wav, sr=16000)
    pcm, sr = read_wav_float32(tmp_wav)
    with contextlib.suppress(Exception):
        tmp_wav.unlink(missing_ok=True)

    chunk_sec = float(cfg.audio_chunk_sec)
    chunk_n = int(sr * chunk_sec)

    # iterate simulated time
    t = 0.0
    audio_idx = 0

    while t <= max(duration, cfg.max_total_time_sec) and not orch.finished:
        # advance clock to t
        clock.t = t

        # feed one video frame (nearest by time)
        fi = int(min(len(frames) - 1, round(t * fps)))
        orch.on_video_frame(frames[fi])

        # feed audio chunks up to current time
        # audio samples correspond to real-time, so send chunk when its end <= t
        while (audio_idx + chunk_n) <= pcm.shape[0] and (
            (audio_idx + chunk_n) / sr
        ) <= t:
            clock.t = audio_idx / sr  # timestamp roughly at chunk start
            chunk = pcm[audio_idx : audio_idx + chunk_n]
            orch.on_audio_pcm(chunk, sr)
            audio_idx += chunk_n

        t += tick

    # find last result
    results = [m for m in msgs if m.get("type") == "result"]
    if not results:
        raise RuntimeError(f"no result produced. last msgs={msgs[-5:]}")
    return results[-1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4", type=str)
    ap.add_argument("--config", default="configs/preflight.yaml")
    ap.add_argument("--config-version-file", default="configs/preflight.version")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    cfg_ver = Path(args.config_version_file).read_text(encoding="utf-8").strip()
    res = replay(Path(args.mp4), args.config, cfg_ver)

    s = json.dumps(res, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(s, encoding="utf-8")
    else:
        print(s)


if __name__ == "__main__":
    main()
