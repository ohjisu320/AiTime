import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from src.contracts.context import FailureReason, QualityFlag, RunContext
from src.contracts.messages import HintMessage, ProgressMessage, ResultMessage
from src.pipelines.stages.aggregate import WindowStats, decide
from src.pipelines.stages.audio_quality import AudioQualityStage
from src.pipelines.stages.face_detect import FaceDetectStage
from src.pipelines.stages.frame_quality import FrameQualityStage
from src.pipelines.stages.roi_validate import ROIValidateStage

logger = logging.getLogger("preflight")


@dataclass
class VideoSample:
    t: float
    luma_mean: float
    low_light: bool
    num_faces: int
    two_faces: bool
    roi1_has: bool
    roi2_has: bool


@dataclass
class AudioSample:
    t: float
    rms_dbfs: float
    noisy: bool


class PreflightOrchestrator:
    """
    Orchestrator responsibilities:
      - stage ordering
      - sampling fps
      - sliding window aggregation
      - sending progress/hint/result
    """

    def __init__(self, ctx: RunContext, send: Callable[[dict], None]) -> None:
        self.ctx = ctx
        self.send = send

        self.frame_stage = FrameQualityStage()
        self.face_stage = FaceDetectStage()
        self.roi_stage = ROIValidateStage()
        self.audio_stage = AudioQualityStage()

        self._video: deque[VideoSample] = deque()
        self._audio: deque[AudioSample] = deque()

        self._t_start = time.monotonic()
        self._last_video_emit_t = 0.0
        self._finished = False

        self._audio_buf = np.zeros((0,), dtype=np.float32)
        self._audio_sr: int | None = None

    @property
    def finished(self) -> bool:
        return self._finished

    def _now(self) -> float:
        return time.monotonic()

    def _prune(self) -> None:
        w = self.ctx.config.window_sec
        t_cut = self._now() - w
        while self._video and self._video[0].t < t_cut:
            self._video.popleft()
        while self._audio and self._audio[0].t < t_cut:
            self._audio.popleft()

    def _window_stats(self) -> WindowStats:
        self._prune()

        v = list(self._video)
        a = list(self._audio)

        def ratio(arr: list[bool]) -> float:
            if not arr:
                return 0.0
            return float(sum(1 for x in arr if x) / len(arr))

        noise_high_ratio = ratio([s.noisy for s in a])
        low_light_ratio = ratio([s.low_light for s in v])
        two_faces_ratio = ratio([s.two_faces for s in v])
        roi1_face_ratio = ratio([s.roi1_has for s in v])
        roi2_face_ratio = ratio([s.roi2_has for s in v])

        avg_rms_dbfs = float(np.mean([s.rms_dbfs for s in a])) if a else -120.0
        avg_luma_mean = float(np.mean([s.luma_mean for s in v])) if v else 0.0

        return WindowStats(
            noise_high_ratio=noise_high_ratio,
            low_light_ratio=low_light_ratio,
            two_faces_ratio=two_faces_ratio,
            roi1_face_ratio=roi1_face_ratio,
            roi2_face_ratio=roi2_face_ratio,
            avg_rms_dbfs=avg_rms_dbfs,
            avg_luma_mean=avg_luma_mean,
        )

    def _maybe_emit(self) -> None:
        stats = self._window_stats()
        seen_seconds = self._now() - self._t_start

        failure_reason, flags, passed = decide(self.ctx, stats, seen_seconds)

        ratios = {
            "noise_high_ratio": stats.noise_high_ratio,
            "low_light_ratio": stats.low_light_ratio,
            "two_faces_ratio": stats.two_faces_ratio,
            "roi1_face_ratio": stats.roi1_face_ratio,
            "roi2_face_ratio": stats.roi2_face_ratio,
        }
        scores = {
            "avg_rms_dbfs": stats.avg_rms_dbfs,
            "avg_luma_mean": stats.avg_luma_mean,
        }

        # progress (0..1)
        progress = float(min(1.0, seen_seconds / self.ctx.config.max_total_time_sec))
        self.send(
            ProgressMessage(
                run_id=self.ctx.repro.run_id,
                progress=progress,
                ratios=ratios,
                scores=scores,
                flags=list(set(flags)),
            ).model_dump()
        )

        # 1. 힌트 우선순위 결정 (가장 심각한 것 하나만)
        hint = None
        if QualityFlag.NOISE_HIGH in flags:
            hint = (
                "주변 소음이 큽니다. TV/대화를 줄이고 조용한 곳에서 다시 시도해 주세요."
            )
        elif QualityFlag.LOW_LIGHT in flags:
            hint = "화면이 어둡습니다. 조명을 켜거나 더 밝은 곳으로 이동해 주세요."
        elif QualityFlag.TOO_MANY_FACES in flags:
            hint = (
                "화면에 사람이 2명보다 많습니다. 검사에는 2명만 나오도록 정리해 주세요."
            )
        elif QualityFlag.TOO_FEW_FACES in flags:
            hint = "화면에 2명이 모두 나오도록 카메라 각도를 조정해 주세요."
        elif (
            QualityFlag.ROI_FACE_MISSING_1 in flags
            or QualityFlag.ROI_FACE_MISSING_2 in flags
        ):
            hint = "지정한 두 영역(ROI)에 얼굴이 들어오도록 위치를 조정해 주세요."

        if hint:
            self.send(
                HintMessage(
                    run_id=self.ctx.repro.run_id,
                    hint=hint,
                    flags=list(set(flags)),
                ).model_dump()
            )

        # final result
        if passed:
            self._finished = True
            self.send(
                ResultMessage(
                    run_id=self.ctx.repro.run_id,
                    passed=True,
                    failure_reason=None,
                    flags=[],
                    ratios=ratios,
                    scores=scores,
                    details={"seen_seconds": seen_seconds},
                ).model_dump()
            )
            return

        # timeout fail is handled by decide()
        if failure_reason == FailureReason.FAIL_TIMEOUT:
            self._finished = True
            self.send(
                ResultMessage(
                    run_id=self.ctx.repro.run_id,
                    passed=False,
                    failure_reason=failure_reason,
                    flags=list(set(flags)),
                    ratios=ratios,
                    scores=scores,
                    details={"seen_seconds": seen_seconds},
                ).model_dump()
            )

    def on_video_frame(self, frame_bgr: np.ndarray) -> None:
        if self._finished:
            return

        # sample fps
        now = self._now()
        min_dt = 1.0 / max(1, self.ctx.config.sample_video_fps)
        if now - self._last_video_emit_t < min_dt:
            return
        self._last_video_emit_t = now

        # stages
        fq = self.frame_stage.run(self.ctx, {"frame_bgr": frame_bgr})
        fd = self.face_stage.run(self.ctx, {"frame_bgr": frame_bgr})
        num_faces = int(fd.payload["num_faces"])

        # 디버그 로그 (30프레임마다)
        self._dbg = getattr(self, "_dbg", 0) + 1
        if self._dbg % 30 == 0:
            logger.info(
                "[%s] num_faces=%d area_ratios=%s",
                self.ctx.repro.run_id,
                num_faces,
                fd.payload["face_area_ratios"],
            )

        H, W = frame_bgr.shape[:2]
        rv = self.roi_stage.run(
            self.ctx, {"frame_wh": (W, H), "face_bboxes": fd.payload["bboxes"]}
        )

        num_faces = int(fd.payload["num_faces"])
        two_faces = num_faces == self.ctx.config.target_faces

        self._video.append(
            VideoSample(
                t=now,
                luma_mean=float(fq.payload["luma_mean"]),
                low_light=bool(fq.payload["low_light"]),
                num_faces=num_faces,
                two_faces=two_faces,
                roi1_has=bool(rv.payload["roi1_has_face"]),
                roi2_has=bool(rv.payload["roi2_has_face"]),
            )
        )

        self._maybe_emit()

    def on_audio_pcm(self, pcm_float32: np.ndarray, sample_rate: int) -> None:
        if self._finished:
            return

        if pcm_float32.size == 0:
            return

        # normalize best-effort
        pcm = pcm_float32.astype(np.float32)
        if pcm.max() > 1.5 or pcm.min() < -1.5:
            pcm = pcm / 32768.0

        # init sr
        if self._audio_sr is None:
            self._audio_sr = int(sample_rate)

        # if sample_rate changes, reset buffer
        if int(sample_rate) != int(self._audio_sr):
            self._audio_sr = int(sample_rate)
            self._audio_buf = np.zeros((0,), dtype=np.float32)

        self._audio_buf = np.concatenate([self._audio_buf, pcm], axis=0)

        # chunk emit
        chunk_sec = float(self.ctx.config.audio_chunk_sec)
        need = int(self._audio_sr * chunk_sec)

        while self._audio_buf.size >= need and not self._finished:
            chunk = self._audio_buf[:need]
            self._audio_buf = self._audio_buf[need:]

            now = self._now()
            aq = self.audio_stage.run(
                self.ctx, {"pcm": chunk, "sample_rate": self._audio_sr}
            )
            self._audio.append(
                AudioSample(
                    t=now,
                    rms_dbfs=float(aq.payload["rms_dbfs"]),
                    noisy=bool(aq.payload["noisy"]),
                )
            )

            self._maybe_emit()
