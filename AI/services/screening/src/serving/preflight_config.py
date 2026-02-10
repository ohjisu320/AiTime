from pathlib import Path

import yaml
from src.contracts.context import ROI, PreflightConfig


def load_preflight_config(path: str = "configs/preflight.yaml") -> PreflightConfig:
    """Load preflight screening config from YAML.

    Keeping this in a dedicated module lets both the legacy aiortc endpoint
    and the LiveKit runner share the exact same config parsing.
    """
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    return PreflightConfig(
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
        # Decision / UX
        min_video_samples=int(raw.get("decision", {}).get("min_video_samples", 10)),
        min_audio_samples=int(raw.get("decision", {}).get("min_audio_samples", 3)),
        progress_interval_sec=float(
            raw.get("decision", {}).get("progress_interval_sec", 0.3)
        ),
        hint_interval_sec=float(raw.get("decision", {}).get("hint_interval_sec", 1.0)),
        pass_hold_sec=float(raw.get("decision", {}).get("pass_hold_sec", 1.0)),
        debug_enabled=bool(raw["debug"].get("enabled", False)),
        debug_save_mismatch_only=bool(raw["debug"].get("save_mismatch_only", True)),
        debug_sample_rate=float(raw["debug"].get("sample_rate", 0.2)),
        debug_save_on_flags=list(raw["debug"].get("save_on_flags", [])),
        debug_artifacts_dir=str(
            raw["debug"].get("artifacts_dir", "artifacts/preflight")
        ),
        logs_enabled=bool(raw.get("logs", {}).get("enabled", True)),
        logs_dir=str(raw.get("logs", {}).get("dir", "artifacts/preflight/logs")),
        stage_log_interval_sec=float(
            raw.get("logs", {}).get("stage_log_interval_sec", 1.0)
        ),
    )
