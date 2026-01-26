from typing import Any

import cv2
import mediapipe as mp

from app.rtn.types import FrameBGR, Landmarks


class FaceMeshMP:
    """
    - trk_mesh: 빠른 tracking 모드 (static_image_mode=False)
    - det_mesh: 초기 검출/복구용 (static_image_mode=True)
    """

    def __init__(
        self,
        refine_landmarks: bool = True,
        det_min_conf: float = 0.3,  # 초기/측면은 낮추는 게 유리
        trk_min_conf: float = 0.5,
        trk_min_track: float = 0.5,
        min_crop_size: int = 160,  # 너무 작으면 업스케일
        upscale_to: int = 256,
    ) -> None:
        self.min_crop_size = int(min_crop_size)
        self.upscale_to = int(upscale_to)

        self.trk_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=trk_min_conf,
            min_tracking_confidence=trk_min_track,
        )

        self.det_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=det_min_conf,
            min_tracking_confidence=0.0,
        )

    def _run(self, mesh: Any, face_bgr: FrameBGR) -> Landmarks | None:
        h, w = face_bgr.shape[:2]
        if h < 2 or w < 2:
            return None

        scale_x = 1.0
        scale_y = 1.0
        img = face_bgr

        if min(h, w) < self.min_crop_size:
            target = self.upscale_to
            img = cv2.resize(
                face_bgr,
                (target, target),
                interpolation=cv2.INTER_LINEAR,
            )
            scale_x = w / target
            scale_y = h / target
            h2, w2 = img.shape[:2]
        else:
            h2, w2 = h, w

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = mesh.process(rgb)
        if not res.multi_face_landmarks:
            return None

        lm = res.multi_face_landmarks[0].landmark
        pts: Landmarks = []
        for p in lm:
            x = p.x * w2
            y = p.y * h2
            x *= scale_x
            y *= scale_y
            pts.append((x, y, p.z))
        return pts

    def landmarks(self, face_bgr: FrameBGR) -> Landmarks | None:
        pts = self._run(self.trk_mesh, face_bgr)
        if pts is not None:
            return pts
        return self._run(self.det_mesh, face_bgr)
