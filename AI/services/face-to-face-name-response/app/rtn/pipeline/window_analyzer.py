import logging
import time
from collections.abc import Callable

import cv2

from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    EmotionConfig,
    GazeSmoothConfig,
    ROIConfig,
    RoleAssignConfig,
    TrackConfig,
)
from app.rtn.debug.renderer import DebugRenderer
from app.rtn.emotion.emotion_recognizer import EmotionRecognizer
from app.rtn.gaze.iris_ratio import GazeEstimatorIrisRatio
from app.rtn.indices import (
    LEFT_EYE_OUTER,
    LEFT_IRIS,
    RIGHT_EYE_OUTER,
    RIGHT_IRIS,
)
from app.rtn.pipeline.results import CallResult
from app.rtn.pipeline.roles import RoleAssignerByArea
from app.rtn.roi.contact import contact_by_raycast
from app.rtn.roi.parent_eye_roi import ParentEyeROIBuilder
from app.rtn.tracking.sort_tracker import SortTracker
from app.rtn.types import BBox, FrameBGR, Landmarks
from app.rtn.utils import crop_face_square
from app.rtn.vision.mp_face_detector import FaceDetectorMP
from app.rtn.vision.mp_facemesh import FaceMeshMP

logger = logging.getLogger("RTNAnalyzer.pipeline.window_analyzer")


class WindowAnalyzer:
    """
    호명 1회 이후 window 구간에서 눈맞춤 + 감정(Emotion) 판정한다.
    """

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
        emotion_cfg: EmotionConfig,
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
        self.emotion_cfg = emotion_cfg
        self.conf_th = conf_th
        self.debug_publish = debug_publish

        # Emotion Recognizer
        self.emotion_recognizer = EmotionRecognizer(emotion_cfg)

    def analyze_call(
        self,
        video_path: str,
        call_idx: int,
        call_start: float,
        call_end: float,
    ) -> CallResult:
        t0 = time.perf_counter()

        # call 단위 분석이므로 트래커/시선추정기의 내부 상태를 초기화
        # 이전 call의 잔상(트랙/스무딩)이 다음 call에 영향 주지 않도록
        self.tracker.reset()
        self.gaze_estimator.reset()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(
                "call open_failed video=%s call=%d",
                video_path,
                call_idx,
            )
            raise RuntimeError(f"비디오 열기 실패: {video_path}")

        # fps는 gaze_duration 누적(dt)과 window 경계 계산에 필요.
        # 메타데이터가 비정상이면(0/NaN) 30fps로 fallback
        fps = cap.get(cv2.CAP_PROP_FPS)
        if self.analysis_cfg.fps_override and self.analysis_cfg.fps_override > 0:
            fps = self.analysis_cfg.fps_override
        fps = (
            fps
            if fps and fps > self.analysis_cfg.fps_min_valid
            else self.analysis_cfg.fallback_fps
        )
        dt = 1.0 / fps

        # 호명 이후를 보니까 분석을 call_end부터 시작
        start_t = max(0.0, call_end)
        end_t = call_end + self.analysis_cfg.window_s
        cap.set(cv2.CAP_PROP_POS_MSEC, start_t * 1000.0)

        logger.info(
            "call start video=%s call=%d call_start=%.3f call_end=%.3f \
                window=[%.3f,%.3f] fps=%.2f",
            video_path,
            call_idx,
            call_start,
            call_end,
            start_t,
            end_t,
            fps,
        )

        role_assigner = RoleAssignerByArea(self.role_cfg.warmup_s)

        consec_contact: int = 0
        first_contact_time: float | None = None
        gaze_duration: float = 0.0

        # Emotion accumulation
        emotion_samples: list[dict[str, float]] = []

        # ADOS Metrics Tracking
        directional_emotions_set: set[str] = set()
        has_happiness_found: bool = False

        role_logged = False
        first_contact_logged = False
        frames = 0

        debug = DebugRenderer(self.analysis_cfg.debug)

        # debug 창 OR MJPEG publish 둘 중 하나라도 켜져있으면 dbg 프레임을 만든다
        debug_mode = self.analysis_cfg.debug or (self.debug_publish is not None)

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                frames += 1

                cur_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                cur_t = cur_msec / 1000.0
                if cur_t > end_t:
                    break

                h, w = frame.shape[:2]
                dbg: FrameBGR | None = frame.copy() if debug_mode else None

                # detect + track
                # - detector는 프레임 단위 noisy할 수 있어 conf_th로 1차 필터링
                # - tracker(SORT)는 bbox를 ID로 연결해 parent/child를 시간축으로 추적
                dets = self.detector.detect(frame)
                dets = [d for d in dets if d[4] >= self.conf_th]
                dets_xyxy: list[BBox] = [(d[0], d[1], d[2], d[3]) for d in dets]
                tracks = self.tracker.update(dets_xyxy)

                # 역할 할당은 초반 몇 초(warmup_s) 동안 트랙 안정화를 기다린 뒤 수행
                # 초기에는 bbox 흔들림/교차가 있어
                # parent/child를 섣불리 확정하면 오류 커짐
                role_assigner.update_warmup(cur_t, start_t, tracks)
                role_assigner.maybe_assign(cur_t, start_t)

                if role_assigner.assigned and not role_logged:
                    logger.info(
                        "role assigned video=%s call=%d t=%.3f parent_id=%s \
                            child_id=%s",
                        video_path,
                        call_idx,
                        cur_t,
                        role_assigner.parent_id,
                        role_assigner.child_id,
                    )
                    role_logged = True

                if debug_mode and dbg is not None:
                    # Debug Tracks
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
                        self._publish_dbg(dbg)

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
                    self._publish_dbg(dbg)
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
                        self._publish_dbg(dbg)

                    if (
                        self.analysis_cfg.debug
                        and dbg is not None
                        and debug.show(dbg, fps)
                    ):
                        break
                    continue

                # crop
                # - parent_margin: 부모는 상대적으로 안정적이라 조금 덜 줌
                # - child_margin: 아이는 얼굴이 더 작고 움직임이 커서 여유를 더 줌
                parent_crop, (pox, poy) = crop_face_square(
                    frame,
                    parent_bbox,
                    margin=0.25,  # parent_margin default
                )
                child_crop, (cox, coy) = crop_face_square(
                    frame,
                    child_bbox,
                    margin=0.4,  # child_margin default
                )

                # =========================================================
                # Emotion Extraction (Added)
                # =========================================================
                current_emotion_str: str = ""
                # DEBUG: 조건 체크
                emo_enable = self.emotion_cfg.enable
                emo_crop_ok = child_crop is not None and child_crop.size > 0
                emo_size_ok = (
                    child_crop.shape[0] >= self.emotion_cfg.min_face_size
                    if emo_crop_ok
                    else False
                )
                emo_skip_ok = frames % self.emotion_cfg.skip_frames == 0

                logger.debug(
                    "Emotion check: enable=%s crop_ok=%s size_ok=%s(shape=%s min=%d) \
                        skip_ok=%s(frame=%d skip=%d)",
                    emo_enable,
                    emo_crop_ok,
                    emo_size_ok,
                    child_crop.shape if emo_crop_ok else None,
                    self.emotion_cfg.min_face_size,
                    emo_skip_ok,
                    frames,
                    self.emotion_cfg.skip_frames,
                )

                current_frame_emotion_dist: dict[str, float] | None = None
                if emo_enable and emo_crop_ok and emo_size_ok and emo_skip_ok:
                    em_dist = self.emotion_recognizer.predict(child_crop)
                    logger.debug("Emotion predict result: %s", em_dist)
                    if em_dist:
                        current_frame_emotion_dist = em_dist
                        emotion_samples.append(em_dist)
                        # Find dominant for debug view
                        dom = max(em_dist, key=em_dist.get)

                        # B6: Check Happiness
                        if dom == "Happiness":
                            has_happiness_found = True
                        score = em_dist[dom]
                        current_emotion_str = f"{dom} {int(score * 100)}%"
                        logger.debug(
                            "Emotion sample added: dom=%s score=%.2f total_samples=%d",
                            dom,
                            score,
                            len(emotion_samples),
                        )

                plm: Landmarks | None = self.facemesh.landmarks(parent_crop)
                clm: Landmarks | None = self.facemesh.landmarks(child_crop)

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
                        self._publish_dbg(dbg)

                    if (
                        self.analysis_cfg.debug
                        and dbg is not None
                        and debug.show(dbg, fps)
                    ):
                        break
                    continue

                # Gaze Estimation
                # 시선 벡터 시작점은 양쪽 눈 바깥꼬리(midpoint)를 사용.
                # iris 중심 단독보다 안정적, head rotation이 있어도 기준점이 덜 흔들림
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
                    clm, (sx, sy), img_w=w, img_h=h
                )

                # Parent ROI
                # - mesh 기반: 눈 윤곽을 더 정확히 잡아 FP를 줄임
                # - bbox fallback: 측면/가림 등으로 mesh 실패 시에도 동작하게 해 FN 줄임
                if plm is not None:
                    hull, eye_mask, roi_mode = self.roi_builder.from_mesh(
                        plm, (pox, poy), img_h=h, img_w=w
                    )
                else:
                    hull, eye_mask, roi_mode = self.roi_builder.from_bbox_fallback(
                        parent_bbox, img_h=h, img_w=w
                    )

                # Raycast
                # 시선 벡터(시작점->end_pt)를 여러 샘플(n_samples: dot)로 쪼개며
                # ROI(mask) 내부를 통과하는지 확인
                # samples가 많을수록 안정적이지만 연산량이 증가
                contact = contact_by_raycast(
                    eye_mask,
                    (sx, sy),
                    end_pt,
                    n_samples=self.contact_cfg.raycast_samples,
                )

                # 접촉 판정은 프레임 단위 노이즈가 있으므로
                # min_contact_frames 연속 True일 때만 성공으로 확정(순간 오탐 억제)
                if contact:
                    consec_contact += 1

                    # gaze_duration은 (접촉으로 판정된 프레임 수 * dt)로 누적
                    # fps가 변해도 시간 단위로 일관되게 집계
                    gaze_duration += dt

                    # B4: Track Directional Emotions (during contact)
                    if current_frame_emotion_dist:
                        dom_c = max(
                            current_frame_emotion_dist,
                            key=current_frame_emotion_dist.get,
                        )
                        directional_emotions_set.add(dom_c)

                    if (
                        first_contact_time is None
                        and consec_contact >= self.contact_cfg.min_contact_frames
                    ):
                        first_contact_time = cur_t
                        if not first_contact_logged:
                            logger.info(
                                "first contact video=%s call=%d t=%.3f latency_s=%.3f \
                                    consec=%d",
                                video_path,
                                call_idx,
                                cur_t,
                                (cur_t - call_end),
                                consec_contact,
                            )
                            first_contact_logged = True
                    status_msg = f"CONTACT ({roi_mode})"
                    status_color = (0, 255, 0)
                else:
                    consec_contact = 0
                    status_msg = f"no contact ({roi_mode})"
                    status_color = (0, 255, 255)

                # overlay는 debug_mode 기준 (스트리밍에도 동일하게 보이게)
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
                    # Emotion Overlay
                    if current_emotion_str:
                        cv2.putText(
                            dbg,
                            current_emotion_str,
                            (cx1, cy2 + 25),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 100, 255),
                            2,
                        )

                    overlay = dbg.copy()
                    overlay[eye_mask > 0] = (0, 255, 0)
                    dbg[:] = cv2.addWeighted(overlay, 0.25, dbg, 0.75, 0)

                    cv2.polylines(dbg, [hull], True, (0, 255, 0), 2)

                    # iris points
                    for idx in LEFT_IRIS + RIGHT_IRIS:
                        x, y, _ = clm[idx]
                        cv2.circle(
                            dbg, (int(x + cox), int(y + coy)), 2, (255, 0, 255), -1
                        )

                    cv2.circle(dbg, (int(sx), int(sy)), 3, (255, 0, 0), -1)
                    cv2.circle(
                        dbg, (int(end_pt[0]), int(end_pt[1])), 5, (0, 0, 255), -1
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
                self._publish_dbg(dbg)

                # 로컬 GUI debug 창은 debug=True일 때만
                if self.analysis_cfg.debug and dbg is not None and debug.show(dbg, fps):
                    break

        finally:
            cap.release()
            debug.close()

        success = first_contact_time is not None
        latency = (first_contact_time - call_end) if success else None

        # Aggregate Emotions
        final_dominant: str | None = None
        final_dist: dict[str, float] = {}
        if emotion_samples:
            # sum all scores
            sums: dict[str, float] = {}
            count = len(emotion_samples)
            for sample in emotion_samples:
                for k, v in sample.items():
                    sums[k] = sums.get(k, 0.0) + v

            # average
            final_dist = {k: v / count for k, v in sums.items()}
            # dominant
            if final_dist:
                final_dominant = max(final_dist, key=final_dist.get)
                final_score = final_dist[final_dominant]
            else:
                final_score = 0.0

        emotion_log_str = (
            f"{final_dominant}({final_score * 100:.1f}%)" if final_dominant else "None"
        )

        logger.info(
            "call done video=%s call=%d success=%s latency_s=%s gaze_s=%.3f \
                emotion=%s frames=%d elapsed_s=%.3f",
            video_path,
            call_idx,
            success,
            latency,
            float(gaze_duration),
            emotion_log_str,
            frames,
            time.perf_counter() - t0,
        )

        if final_dist:
            # Sort for better readability
            sorted_dist = dict(
                sorted(final_dist.items(), key=lambda item: item[1], reverse=True)
            )
            logger.info("  -> Emotion Dist: %s", sorted_dist)

        return CallResult(
            call_index=call_idx,
            call_start=call_start,
            call_end=call_end,
            success=success,
            latency_s=latency,
            gaze_duration_s=float(gaze_duration),
            dominant_emotion=final_dominant,
            emotion_distribution=final_dist,
            meta={
                "emotion_model": self.emotion_cfg.model_name,
                "emotion_samples_count": len(emotion_samples),
                "timestamp_ms": int(time.time() * 1000),
            },
            # ADOS
            directional_emotions=list(directional_emotions_set),
            has_happiness=has_happiness_found,
        )

    def _publish_dbg(self, dbg: FrameBGR | None) -> None:
        if self.debug_publish is not None and dbg is not None:
            self.debug_publish(dbg)
