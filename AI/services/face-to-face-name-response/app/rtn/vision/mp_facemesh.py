from typing import Any

import cv2
import mediapipe as mp

from app.rtn.types import FrameBGR, Landmarks


class FaceMeshMP:
    """
    MediaPipe FaceMesh 래퍼.

    - trk_mesh(static_image_mode=False): 연속 프레임에서 tracking 성능/속도가 좋음
    - det_mesh(static_image_mode=True): tracking이 깨졌을 때 재검출/복구용

    - Landmarks는 crop 이미지 좌표계 기준 (x,y,z) 리스트이며, (x,y)는 픽셀 단위
    - landmark가 없으면 None 반환
    """

    def __init__(
        self,
        refine_landmarks: bool = True,
        det_min_conf: float = 0.3,  # 초기/측면은 낮추는 게 유리
        trk_min_conf: float = 0.5,  # 너무 낮으면 불안정해짐
        trk_min_track: float = 0.5,
        min_crop_size: int = 160,  # crop은 적당히 커야 함. 너무 작으면 업스케일 필요
        upscale_to: int = 256,
    ) -> None:
        self.min_crop_size = int(min_crop_size)
        self.upscale_to = int(upscale_to)

        # tracking 모드: 이전 프레임 정보를 활용해 landmark를 더 빠르게/안정적으로 추정
        self.trk_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=trk_min_conf,
            min_tracking_confidence=trk_min_track,
        )

        # detection 모드: 매 호출마다 독립적으로 검출(느리지만 깨지면 복구에 유리)
        self.det_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=det_min_conf,
            min_tracking_confidence=0.0,  # 깨졌으니까
        )

    def _run(self, mesh: Any, face_bgr: FrameBGR) -> Landmarks | None:
        h, w = face_bgr.shape[:2]
        if h < 2 or w < 2:
            return None

        # 업스케일:
        # crop이 너무 작으면(특히 아이 얼굴/원거리) FaceMesh가 landmark를 놓칠 수 있어
        # 일정 크기로 키워 추정 안정성을 높임
        # 단, 결과는 원래 crop 좌표계로 되돌리기 위해 scale을 적용
        scale_x = 1.0
        scale_y = 1.0
        img = face_bgr

        # NOTE: face_bgr는 상위에서 square crop으로 만들어진다는 가정(crop_face_square)
        # 비정사각 입력이 들어오면 (target,target) resize가 왜곡 가능
        if min(h, w) < self.min_crop_size:
            target = self.upscale_to
            img = cv2.resize(
                face_bgr,
                (target, target),
                interpolation=cv2.INTER_LINEAR,
            )
            # resize된 이미지 좌표(w2,h2)를 원래 crop 좌표(w,h)로 역변환하기 위한 스케일
            scale_x = w / target
            scale_y = h / target
            h2, w2 = img.shape[:2]
        else:
            h2, w2 = h, w

        # MediaPipe는 RGB 입력 기대(OpenCV는 BGR)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = mesh.process(rgb)
        if not res.multi_face_landmarks:
            return None

        # MediaPipe landmark는 정규화 좌표(p.x,p.y in [0,1])이므로 픽셀로 변환
        # 업스케일을 했다면 scale_x/scale_y로 원래 crop 좌표계로 되돌림
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
        # 1) tracking 모드로 빠르게 시도
        pts = self._run(self.trk_mesh, face_bgr)
        if pts is not None:
            return pts

        # 2) 실패하면 detection 모드로 복구(초기 프레임/측면/가림 케이스 대비)
        return self._run(self.det_mesh, face_bgr)
