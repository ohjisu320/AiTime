import logging
import os
import tempfile
import time
from collections.abc import Callable
from typing import Any

import numpy as np

from app.rtn.audio.segments import vad_segments_from_video
from app.rtn.audio.vad_silero import SileroVAD
from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    EmotionConfig,
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
from app.rtn.vision.openvino_face_detector import OpenVINOFaceDetector
from app.rtn.vision.yolo_face_detector import YOLOFaceDetector

logger = logging.getLogger("RTNAnalyzer.pipeline.video_analyzer")


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
        emotion_cfg: EmotionConfig,
        conf_th: float,
        debug_publish: Callable[[FrameBGR], None] | None = None,
    ) -> None:
        self.vad_cfg = vad_cfg
        self.analysis_cfg = analysis_cfg
        self.emotion_cfg = emotion_cfg

        self.vad = SileroVAD(vad_cfg)

        # Detector selection
        if face_cfg.model_selection == 2:
            self.detector = OpenVINOFaceDetector(face_cfg.yolo_cfg)
        elif face_cfg.model_selection == 1:
            self.detector = YOLOFaceDetector(face_cfg.yolo_cfg)
        else:
            self.detector = FaceDetectorMP(face_cfg)

        # FaceMeshMP는 기본 파라미터 사용 (별도 config 없음)
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
            emotion_cfg=emotion_cfg,
            conf_th=conf_th,
            debug_publish=debug_publish,
        )

    def analyze(self, video_path: str) -> dict[str, Any]:
        """
        비디오 1개를 분석해 결과를 dict로 반환한다.

        파이프라인
        - VAD로 '호명 구간(세그먼트)'을 검출
        - 각 세그먼트마다 window_analyzer로 반응(성공/지연/유지)을 계산
        - summary/per_call/params 형태로 집계

        계약/주의
        - VAD 과정에서 임시 wav 추출을 위해 디스크 I/O가 발생(tmp_dir 사용).
        - segs가 0개일 수 있으며, 이때 per_call은 빈 리스트이고 avg_latency_s는 None.
        - 오래 걸리는 작업으로 서비스에서 event loop 블로킹 방지를 위해 threadpool 실행
        """
        t0 = time.perf_counter()
        logger.info("analyze start video_path=%s", video_path)

        # VAD 단계에서 wav 추출이 필요해서 tmp_dir를 사용한다.
        with tempfile.TemporaryDirectory(prefix="rtn_vad_") as tmp_dir:
            segs = vad_segments_from_video(
                video_path=video_path,
                vad=self.vad,
                cfg=self.vad_cfg,
                tmp_dir=tmp_dir,
            )

        logger.info(
            "vad segments video=%s count=%d",
            os.path.basename(video_path),
            len(segs),
        )

        results: list[CallResult] = []
        for i, (s, e) in enumerate(segs, start=1):
            t_call = time.perf_counter()

            # 각 호명 구간의 (끝 시점 e) 이후 일정 window를 분석해
            # 반응 여부/지연(latency)/유지(gaze_duration)를 계산한다.
            r = self.window_analyzer.analyze_call(
                video_path,
                call_idx=i,
                call_start=s,
                call_end=e,
            )
            results.append(r)

            logger.info(
                "call done video=%s call=%d start=%.3f end=%.3f success=%s \
                    latency_s=%s gaze_s=%.3f elapsed_s=%.3f",
                os.path.basename(video_path),
                i,
                s,
                e,
                r.success,
                r.latency_s,
                r.gaze_duration_s,
                time.perf_counter() - t_call,
            )

        # segs가 0개일 수 있다:
        # - success_count=0, total_call_count=0
        # - latencies가 비어 avg_latency=None
        total_calls = len(results)
        success_calls = sum(1 for r in results if r.success)
        total_gaze = sum(r.gaze_duration_s for r in results)
        latencies = [r.latency_s for r in results if r.latency_s is not None]
        avg_latency = float(np.mean(latencies)) if latencies else None

        logger.info(
            "analyze done video=%s elapsed_s=%.3f success=%d/%d avg_latency_s=%s \
                total_gaze_s=%.3f",
            os.path.basename(video_path),
            time.perf_counter() - t0,
            int(success_calls),
            int(total_calls),
            avg_latency,
            float(total_gaze),
        )

        # ADOS Aggregation
        # B1: Eye Contact (0-3 scale based on frequency)
        b1_score = min(3, int(success_calls))

        # B4: Facial Expressions (diversity during contact)
        all_directional_emotions = set()
        for r in results:
            if r.directional_emotions:
                all_directional_emotions.update(r.directional_emotions)

        # Exclude Neutral
        all_directional_emotions.discard("Neutral")

        unique_emotion_count = len(all_directional_emotions)
        if unique_emotion_count >= 3:
            b4_score = 0
        elif unique_emotion_count == 2:
            b4_score = 1
        elif unique_emotion_count == 1:
            b4_score = 2
        else:
            b4_score = 3

        # B6: Happiness (at least once)
        b6_happiness = any(r.has_happiness for r in results)

        # B18: Response to Name (at least once success)
        b18_response = success_calls > 0

        ados_result = {
            "B1": b1_score,
            "B4": b4_score,
            "B6": b6_happiness,
            "B18": b18_response,
        }

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
            "ADOS": ados_result,
            "per_call": [
                {
                    "call_index": r.call_index,
                    "call_start_s": r.call_start,
                    "call_end_s": r.call_end,
                    "success": r.success,
                    "latency_s": r.latency_s,
                    "gaze_duration_s": r.gaze_duration_s,
                    "dominant_emotion": r.dominant_emotion,
                    "emotion_distribution": r.emotion_distribution,
                    "directional_emotions": r.directional_emotions,
                    "has_happiness": r.has_happiness,
                }
                for r in results
            ],
        }


def analyze_video(video_path: str, analyzer: VideoAnalyzer) -> dict[str, Any]:
    t0 = time.time()
    out = analyzer.analyze(video_path)
    out["elapsed_s"] = float(time.time() - t0)
    return out
