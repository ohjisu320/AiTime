import os
import time
from collections.abc import Callable
from typing import Any

import numpy as np

from app.rtn.audio.segments import vad_segments_from_video
from app.rtn.audio.vad_silero import SileroVAD
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
from app.rtn.pipeline.results import CallResult
from app.rtn.pipeline.window_analyzer import WindowAnalyzer
from app.rtn.types import FrameBGR
from app.rtn.vision.mp_face_detector import FaceDetectorMP
from app.rtn.vision.mp_facemesh import FaceMeshMP


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
        debug_publish: Callable[[FrameBGR], None] | None = None,
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
            debug_publish=debug_publish,
        )

    def analyze(self, video_path: str) -> dict[str, Any]:
        tmp_dir = os.path.join(
            os.path.dirname(os.path.abspath(video_path)),
            self.vad_cfg.tmp_dirname,
        )

        segs = vad_segments_from_video(
            video_path=video_path,
            vad=self.vad,
            cfg=self.vad_cfg,
            tmp_dir=tmp_dir,
        )

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


def analyze_video(video_path: str, analyzer: VideoAnalyzer) -> dict[str, Any]:
    t0 = time.time()
    out = analyzer.analyze(video_path)
    out["elapsed_s"] = float(time.time() - t0)
    return out
