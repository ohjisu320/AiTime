from collections.abc import Callable

import cv2

from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    GazeSmoothConfig,
    ROIConfig,
    RoleAssignConfig,
    TrackConfig,
)
from app.rtn.debug.renderer import DebugRenderer
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


class WindowAnalyzer:
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
        self.conf_th = conf_th
        self.debug_publish = debug_publish

    def analyze_call(
        self,
        video_path: str,
        call_idx: int,
        call_start: float,
        call_end: float,
    ) -> CallResult:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"비디오 열기 실패: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if self.analysis_cfg.fps_override and self.analysis_cfg.fps_override > 0:
            fps = self.analysis_cfg.fps_override
        fps = fps if fps and fps > 1e-3 else 30.0
        dt = 1.0 / fps

        start_t = max(0.0, call_end)
        end_t = call_end + self.analysis_cfg.window_s
        cap.set(cv2.CAP_PROP_POS_MSEC, start_t * 1000.0)

        role_assigner = RoleAssignerByArea(self.role_cfg.warmup_s)

        consec_contact: int = 0
        first_contact_time: float | None = None
        gaze_duration: float = 0.0

        debug = DebugRenderer(self.analysis_cfg.debug)

        # debug 창 OR MJPEG publish 둘 중 하나라도 켜져있으면 dbg 프레임을 만든다
        debug_mode = self.analysis_cfg.debug or (self.debug_publish is not None)

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                cur_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                cur_t = cur_msec / 1000.0
                if cur_t > end_t:
                    break

                h, w = frame.shape[:2]
                dbg: FrameBGR | None = frame.copy() if debug_mode else None

                # detect + track
                dets = self.detector.detect(frame)
                dets = [d for d in dets if d[4] >= self.conf_th]
                dets_xyxy: list[BBox] = [(d[0], d[1], d[2], d[3]) for d in dets]
                tracks = self.tracker.update(dets_xyxy)

                role_assigner.update_warmup(cur_t, start_t, tracks)
                role_assigner.maybe_assign(cur_t, start_t)

                if debug_mode and dbg is not None:
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
                parent_crop, (pox, poy) = crop_face_square(
                    frame, parent_bbox, margin=0.25
                )
                child_crop, (cox, coy) = crop_face_square(
                    frame, child_bbox, margin=0.40
                )

                # facemesh
                plm: Landmarks | None = self.facemesh.landmarks(parent_crop)  # optional
                clm: Landmarks | None = self.facemesh.landmarks(child_crop)  # required
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

                # child gaze start point: outer corners mid
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

                # parent ROI
                if plm is not None:
                    hull, eye_mask, roi_mode = self.roi_builder.from_mesh(
                        plm, (pox, poy), img_h=h, img_w=w
                    )
                else:
                    hull, eye_mask, roi_mode = self.roi_builder.from_bbox_fallback(
                        parent_bbox, img_h=h, img_w=w
                    )

                contact = contact_by_raycast(
                    eye_mask,
                    (sx, sy),
                    end_pt,
                    n_samples=self.contact_cfg.raycast_samples,
                )

                if contact:
                    consec_contact += 1
                    gaze_duration += dt
                    if (
                        first_contact_time is None
                        and consec_contact >= self.contact_cfg.min_contact_frames
                    ):
                        first_contact_time = cur_t
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

        return CallResult(
            call_index=call_idx,
            call_start=call_start,
            call_end=call_end,
            success=success,
            latency_s=latency,
            gaze_duration_s=float(gaze_duration),
        )

    def _publish_dbg(self, dbg: FrameBGR | None) -> None:
        if self.debug_publish is not None and dbg is not None:
            self.debug_publish(dbg)
