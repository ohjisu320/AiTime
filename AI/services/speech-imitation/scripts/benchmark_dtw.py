import os
import sys
import time

import librosa
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.models.imitation_similarity import AudioSimilarityDTW


def benchmark(
    stim_path: str, resp_path: str, radii: list[int]
) -> list[dict[str, float | int]]:
    print(f"Loading files:\n  Stim: {stim_path}\n  Resp: {resp_path}")

    # Load audio
    y_stim, sr_stim = librosa.load(stim_path, sr=16000)
    y_resp, sr_resp = librosa.load(resp_path, sr=16000)

    scorer = AudioSimilarityDTW()
    settings = get_settings()

    # Warmup
    _ = scorer.score(y_stim, y_resp, 16000)

    results = []

    print(
        f"\n{'Radius':<10} | ",
        f"{'ns/sample':<15} | {'Cost':<10} | {'Sim':<10} | {'Time(ms)':<10}",
    )
    print("-" * 65)

    for r in radii:
        # Patch setting
        settings.DTW_RADIUS = r

        # Measure time
        start_time = time.perf_counter()
        res = scorer.score(y_stim, y_resp, 16000)
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000

        # Full DTW (Radius=1) is baseline
        label = "Full" if r <= 1 else str(r)

        print(
            f"{label:<10} | {res.used_frames_a}x{res.used_frames_b:<9} |",
            f" {res.dtw_cost:.4f}     | {res.similarity:.4f}     | {duration_ms:.2f}",
        )

        results.append(
            {
                "radius": r,
                "time_ms": duration_ms,
                "similarity": res.similarity,
                "cost": res.dtw_cost,
            }
        )

    return results


if __name__ == "__main__":
    # Default paths
    base_dir = os.path.dirname(__file__)
    # Looking for debug_output in project root
    debug_dir = os.path.join(base_dir, "..", "debug_output")

    # Find first OK pair
    stim_file = os.path.join(debug_dir, "trial01_rep01_OK_stim.wav")
    resp_file = os.path.join(debug_dir, "trial01_rep01_OK_resp.wav")

    if not os.path.exists(stim_file) or not os.path.exists(resp_file):
        print("Default debug files not found. Creating dummy audio for benchmark.")
        # Create dummy audio
        sr = 16000
        y_stim = np.random.uniform(-0.5, 0.5, sr * 2)  # 2 sec
        import soundfile as sf

        sf.write("benchmark_stim.wav", y_stim, sr)
        sf.write("benchmark_resp.wav", y_stim, sr)  # Perfect match
        stim_file = "benchmark_stim.wav"
        resp_file = "benchmark_resp.wav"

    radii = [1, 5, 10, 20, 30, 50, 100]
    benchmark(stim_file, resp_file, radii)
