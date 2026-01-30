import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from src.contracts.context import FailureReason, QualityFlag, RunContext
from src.contracts.messages import HintMessage, ProgressMessage, ResultMessage
from src.monitoring.artifacts import DebugArtifactSaver
from src.monitoring.run_logger import JsonlRunLogger
from src.pipelines.stages.aggregate import WindowStats
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


def _pick_failure_reason(flags: list[QualityFlag]) -> FailureReason | None:
    # 대표 원인 우선순위 (UX 단순화)
    if QualityFlag.NOISE_HIGH in flags:
        return FailureReason.FAIL_NOISE
    if QualityFlag.LOW_LIGHT in flags:
        return FailureReason.FAIL_LOW_LIGHT
    if (QualityFlag.TOO_FEW_FACES in flags) or (QualityFlag.TOO_MANY_FACES in flags):
        return FailureReason.FAIL_FACE_COUNT
    if (QualityFlag.ROI_FACE_MISSING_1 in flags) or (
        QualityFlag.ROI_FACE_MISSING_2 in flags
    ):
        return FailureReason.FAIL_ROI_MISMATCH
    return None


def _make_hint(flags: list[QualityFlag]) -> str:
    if not flags:
        return ""

    # 상세 분기: TooFew vs TooMany는 반드시 구분
    if QualityFlag.NOISE_HIGH in flags:
        return "주변 소음이 큽니다. TV/대화를 줄이고 조용한 장소로 이동해 주세요."
    if QualityFlag.LOW_LIGHT in flags:
        return "화면이 어둡습니다. 조명을 켜고 역광(창문 뒤)을 피해서 촬영해 주세요."
    if QualityFlag.TOO_MANY_FACES in flags:
        return "화면에 사람이 2명보다 많습니다. 검사에는 2명만 나오도록 정리해 주세요."
    if QualityFlag.TOO_FEW_FACES in flags:
        return "화면에 2명이 모두 나오도록 카메라를 뒤로/위치 조정해 주세요."
    if (
        QualityFlag.ROI_FACE_MISSING_1 in flags
        or QualityFlag.ROI_FACE_MISSING_2 in flags
    ):
        miss = []
        if QualityFlag.ROI_FACE_MISSING_1 in flags:
            miss.append("왼쪽")
        if QualityFlag.ROI_FACE_MISSING_2 in flags:
            miss.append("오른쪽")
        side = "/".join(miss) if miss else "지정된"
        return f"{side} 영역(ROI)에 얼굴이 들어오도록 위치를 맞춰 주세요."
    return "조금만 더 위치/환경을 조정해 주세요."


class PreflightOrchestrator:
    """
    Orchestrator responsibilities:
      - stage ordering
      - sampling fps
      - sliding window aggregation
      - sending progress/hint/result
    """

    def __init__(
        self,
        ctx: RunContext,
        send: Callable[[dict], None],
        run_logger: JsonlRunLogger | None = None,
        artifact_saver: DebugArtifactSaver | None = None,
    ) -> None:
        self.ctx = ctx
        self.send = send
        self.logger = run_logger
        self.artifact_saver = artifact_saver
        self._last_stage_log_t: dict[str, float] = {}

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

        # 상태 필드
        self._last_progress_sent_t = 0.0
        self._last_hint_sent_t = 0.0
        self._last_flags_sig: tuple[str, ...] = ()
        self._last_hint_text: str = ""
        self._pass_start_t: float | None = None

        if self.logger:
            self.logger.log(
                "lifecycle_start",
                {
                    "repro": self.ctx.repro.model_dump(),
                    "task_type": self.ctx.config.task_type,
                    "config": self.ctx.config.model_dump(),
                },
            )

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
            video_count=len(v),
            audio_count=len(a),
            noise_high_ratio=noise_high_ratio,
            low_light_ratio=low_light_ratio,
            two_faces_ratio=two_faces_ratio,
            roi1_face_ratio=roi1_face_ratio,
            roi2_face_ratio=roi2_face_ratio,
            avg_rms_dbfs=avg_rms_dbfs,
            avg_luma_mean=avg_luma_mean,
        )

    def _log_stage(self, name: str, out: Any, extra: dict | None = None) -> None:
        if not self.logger:
            return
        now = self._now()
        interval = getattr(self.ctx.config, "stage_log_interval_sec", 1.0)
        last = self._last_stage_log_t.get(name, 0.0)
        if now - last < interval:
            return
        self._last_stage_log_t[name] = now

        self.logger.log(
            "stage",
            {
                "stage_name": name,
                "latency_ms": out.stage_metrics.latency_ms,
                "success": out.stage_metrics.success,
                "extra": {**out.stage_metrics.extra, **(extra or {})},
                "quality_flags": [f.value for f in out.quality_flags],
            },
        )

    def _finish_lifecycle(self, seen_seconds: float) -> None:
        if self.logger:
            self.logger.log("lifecycle_end", {"seen_seconds": seen_seconds})
            self.logger.close()

    def _maybe_emit(self) -> None:
        now = self._now()
        seen_seconds = now - self._t_start

        # ---- 0) 워밍업: 샘플 부족이면 FAIL 판단/힌트 남발 금지 ----
        min_v = getattr(self.ctx.config, "min_video_samples", 10)
        min_a = getattr(self.ctx.config, "min_audio_samples", 3)

        if len(self._video) < min_v or len(self._audio) < min_a:
            # progress만 천천히 보내기
            interval = getattr(self.ctx.config, "progress_interval_sec", 0.3)
            if now - self._last_progress_sent_t >= interval:
                progress = float(
                    min(1.0, seen_seconds / self.ctx.config.max_total_time_sec)
                )
                self.send(
                    ProgressMessage(
                        run_id=self.ctx.repro.run_id,
                        progress=progress,
                        ratios={},
                        scores={},
                        flags=[],
                    ).model_dump()
                )
                self._last_progress_sent_t = now
            return

        # ---- 1) 윈도우 통계 계산 ----
        stats = self._window_stats()

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
        self._last_ratios = ratios
        self._last_scores = scores

        # ---- 2) 현재 flags 계산 (윈도우 기반) ----
        flags: list[QualityFlag] = []

        if stats.noise_high_ratio > self.ctx.config.audio_noise_high_ratio_max:
            flags.append(QualityFlag.NOISE_HIGH)

        if stats.low_light_ratio > self.ctx.config.video_low_light_ratio_max:
            flags.append(QualityFlag.LOW_LIGHT)

        if stats.two_faces_ratio < self.ctx.config.faces_two_faces_ratio_min:
            v = list(self._video)
            avg_faces = sum(s.num_faces for s in v) / max(1, len(v))
            if avg_faces > self.ctx.config.target_faces:
                flags.append(QualityFlag.TOO_MANY_FACES)
            else:
                flags.append(QualityFlag.TOO_FEW_FACES)

        if stats.roi1_face_ratio < self.ctx.config.roi_face_ratio_min:
            flags.append(QualityFlag.ROI_FACE_MISSING_1)
        if stats.roi2_face_ratio < self.ctx.config.roi_face_ratio_min:
            flags.append(QualityFlag.ROI_FACE_MISSING_2)

        # ---- 3) PASS 여부 + PASS hold(깜빡임 방지) ----
        instant_pass = (
            stats.noise_high_ratio <= self.ctx.config.audio_noise_high_ratio_max
            and stats.low_light_ratio <= self.ctx.config.video_low_light_ratio_max
            and stats.two_faces_ratio >= self.ctx.config.faces_two_faces_ratio_min
            and stats.roi1_face_ratio >= self.ctx.config.roi_face_ratio_min
            and stats.roi2_face_ratio >= self.ctx.config.roi_face_ratio_min
        )

        pass_hold_sec = getattr(self.ctx.config, "pass_hold_sec", 1.0)
        if instant_pass:
            if self._pass_start_t is None:
                self._pass_start_t = now
            held = (now - self._pass_start_t) >= pass_hold_sec
        else:
            self._pass_start_t = None
            held = False

        # ---- 4) progress 메시지 (스팸 방지) ----
        progress_interval = getattr(self.ctx.config, "progress_interval_sec", 0.3)
        flags_sig = tuple(sorted([f.value for f in flags]))

        if (now - self._last_progress_sent_t >= progress_interval) or (
            flags_sig != self._last_flags_sig
        ):
            progress = float(
                min(1.0, seen_seconds / self.ctx.config.max_total_time_sec)
            )
            self.send(
                ProgressMessage(
                    run_id=self.ctx.repro.run_id,
                    progress=progress,
                    ratios=ratios,
                    scores=scores,
                    flags=flags,
                ).model_dump()
            )
            if self.logger:
                self.logger.log(
                    "progress",
                    {
                        "progress": progress,
                        "ratios": ratios,
                        "scores": scores,
                        "flags": [f.value for f in flags],
                    },
                )
            self._last_progress_sent_t = now
            self._last_flags_sig = flags_sig

        # ---- 5) hint 메시지 (대표 원인 + 행동 가이드, 스팸 방지) ----
        hint_interval = getattr(self.ctx.config, "hint_interval_sec", 1.0)
        hint = _make_hint(flags)
        if hint and (
            (now - self._last_hint_sent_t >= hint_interval)
            or (hint != self._last_hint_text)
        ):
            self.send(
                HintMessage(
                    run_id=self.ctx.repro.run_id,
                    hint=hint,
                    flags=flags,
                ).model_dump()
            )
            if self.logger:
                self.logger.log(
                    "hint", {"hint": hint, "flags": [f.value for f in flags]}
                )
            self._last_hint_sent_t = now
            self._last_hint_text = hint

        # ---- 6) 최종 PASS/FAIL 결정 ----
        if held:
            self._finished = True
            self.send(
                ResultMessage(
                    run_id=self.ctx.repro.run_id,
                    passed=True,
                    failure_reason=None,
                    flags=[],
                    ratios=ratios,
                    scores=scores,
                    details={
                        "seen_seconds": seen_seconds,
                        "pass_hold_sec": pass_hold_sec,
                    },
                ).model_dump()
            )
            if self.logger:
                self.logger.log(
                    "result",
                    {
                        "passed": True,
                        "failure_reason": None,
                        "flags": [],
                        "ratios": ratios,
                        "scores": scores,
                        "details": {
                            "seen_seconds": seen_seconds,
                            "pass_hold_sec": pass_hold_sec,
                        },
                    },
                )
            if self.artifact_saver:
                self.artifact_saver.maybe_save(
                    passed=True,
                    flags=[],
                    failure_reason=None,
                    details={
                        "seen_seconds": seen_seconds,
                        "pass_hold_sec": pass_hold_sec,
                    },
                )
            self._finish_lifecycle(seen_seconds)
            return

        # timeout FAIL
        if seen_seconds >= self.ctx.config.max_total_time_sec:
            self._finished = True
            fr = FailureReason.FAIL_TIMEOUT
            rep_fr = _pick_failure_reason(flags)
            if self.logger:
                self.logger.log(
                    "result",
                    {
                        "passed": False,
                        "failure_reason": fr.value,
                        "flags": [f.value for f in flags],
                        "ratios": ratios,
                        "scores": scores,
                        "details": {
                            "seen_seconds": seen_seconds,
                            "representative_failure": rep_fr.value if rep_fr else None,
                        },
                    },
                )
            if self.artifact_saver:
                self.artifact_saver.maybe_save(
                    passed=False,
                    flags=[f.value for f in flags],
                    failure_reason=fr.value,
                    details={
                        "seen_seconds": seen_seconds,
                        "representative_failure": rep_fr.value if rep_fr else None,
                    },
                )
            self._finish_lifecycle(seen_seconds)

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

        # stage logs (video) - 샘플링 간격(stage_log_interval_sec)에 따라 기록됨
        self._log_stage("frame_quality", fq)
        self._log_stage("face_detect", fd, extra={"num_faces": num_faces})
        self._log_stage("roi_validate", rv)

        # artifact saver - 마지막 프레임 스냅샷 저장(실패 시 저장용)
        if self.artifact_saver:
            self.artifact_saver.update_frame(
                frame_bgr=frame_bgr,
                bboxes=fd.payload["bboxes"],
                ratios=getattr(self, "_last_ratios", {}),
                scores=getattr(self, "_last_scores", {}),
            )

        # video sample 기록
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

        if self.artifact_saver:
            self.artifact_saver.update_frame(
                frame_bgr,
                bboxes=fd.payload["bboxes"],
                ratios=getattr(self, "_last_ratios", {}),
                scores=getattr(self, "_last_scores", {}),
            )

        self._log_stage("frame_quality", fq)
        self._log_stage("face_detect", fd)
        self._log_stage("roi_validate", rv)

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
            self._log_stage("audio_quality", aq)

            self._maybe_emit()
