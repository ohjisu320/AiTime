import cv2
import numpy as np
import numpy.typing as npt

from app.rtn.config import ROIConfig
from app.rtn.indices import LEFT_EYE_CONTOUR, RIGHT_EYE_CONTOUR
from app.rtn.types import BBox, Landmarks, MaskU8
from app.rtn.utils import clamp


class ParentEyeROIBuilder:
    """
    부모의 '눈(eye) ROI 마스크'를 생성한다.

    - mesh 기반(from_mesh):
        FaceMesh landmark로 좌/우 눈 윤곽을 모아 convex hull을 만들고 mask로 변환
      -> 정밀도가 높아 FP(오탐)를 줄이는 데 유리
    - bbox fallback(from_bbox_fallback):
        FaceMesh 실패 시 얼굴 bbox 상단부에 눈이 있을 법한 영역을 ellipse로 근사
      -> mesh가 없더라도 FN(미탐)을 줄이는 보수적 fallback

    output:
    - hull/rect: ROI 윤곽(디버깅 시 시각화용)
    - mask: img_h x img_w의 uint8 마스크(ROI=255)
    - mode: "mesh_eye" 또는 "bbox_fallback"
    """

    def __init__(self, cfg: ROIConfig) -> None:
        self.cfg = cfg

    @staticmethod
    def _mask_from_hull(
        hull: npt.NDArray[np.int32],
        img_h: int,
        img_w: int,
        dilate_px: int,
    ) -> MaskU8:
        # hull(다각형)을 마스크로 채운 뒤 dilation으로 여유를 준다.
        # - FaceMesh 좌표는 프레임마다 약간 흔들릴 수 있어 ROI를 강하게 잡으면 FN 증가
        # - dilation은 '여유 버퍼' 역할(판정 안정화)
        mask = np.zeros((img_h, img_w), dtype=np.uint8)
        cv2.fillConvexPoly(mask, hull, 255)

        # OpenCV morphology는 보통 홀수 크기 커널이 자연스러움
        # 중심점이 존재 하는 거 때문에 보통 홀수로 사용
        # dilate_px를 받아 홀수 커널(k)로 변환
        k = max(3, int(dilate_px) // 2 * 2 + 1)
        kernel = np.ones((k, k), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        return mask

    def from_mesh(
        self,
        plm: Landmarks,
        offset_xy: tuple[int, int],
        img_h: int,
        img_w: int,
    ) -> tuple[npt.NDArray[np.int32], MaskU8, str]:
        # plm은 crop 좌표계의 landmark이므로, offset_xy(원본에서 crop 좌상단)를 더해
        # 원본 프레임 좌표계로 변환
        ox, oy = offset_xy
        idxs = LEFT_EYE_CONTOUR + RIGHT_EYE_CONTOUR

        # 화면 밖으로 나간 좌표는 clip하여 convexHull/fillConvexPoly로 안정화
        pts = np.array(
            [[plm[i][0] + ox, plm[i][1] + oy] for i in idxs], dtype=np.float32
        )
        pts[:, 0] = np.clip(pts[:, 0], 0, img_w - 1)
        pts[:, 1] = np.clip(pts[:, 1], 0, img_h - 1)

        # 좌/우 눈 contour 포인트를 합친 뒤 convex hull로 하나의 ROI 윤곽을 만듦
        # (눈 윤곽 점 순서가 완전하지 않아도 hull이면 안정적으로 다각형이 됨)
        hull = cv2.convexHull(pts.astype(np.int32))
        mask = self._mask_from_hull(hull, img_h, img_w, self.cfg.mesh_dilate_px)
        return hull, mask, "mesh_eye"

    def from_bbox_fallback(
        self,
        parent_bbox_xyxy: BBox,
        img_h: int,
        img_w: int,
    ) -> tuple[npt.NDArray[np.int32], MaskU8, str]:
        # FaceMesh가 없을 때는 얼굴 bbox 내부에서 눈이 있을 법한 상단 영역을 근사
        # 휴리스틱(비율)은 정면 얼굴 기준 경험값, 각도/가림/카메라 위치에 따라 오차 존재
        # 목적은 정밀한 눈 윤곽이 아니라
        # eye-contact 판정에서 ROI를 완전히 잃지 않는 것(FN 감소)
        x1, y1, x2, y2 = parent_bbox_xyxy
        x1 = float(clamp(x1, 0, img_w - 1))
        x2 = float(clamp(x2, 0, img_w - 1))
        y1 = float(clamp(y1, 0, img_h - 1))
        y2 = float(clamp(y2, 0, img_h - 1))

        bw = max(1.0, x2 - x1)
        bh = max(1.0, y2 - y1)

        # 얼굴 bbox 내부에서 눈이 있을 법한(이마~코) 상단 영역을 ellipse로 근사
        # - x: 좌우 15%~85% (볼/귀 영역 일부 제외)
        # - y: 위 18%~55% (눈썹~눈~코 윗부분 근처)
        rx1 = int(clamp(x1 + 0.15 * bw, 0, img_w - 1))
        rx2 = int(clamp(x1 + 0.85 * bw, 0, img_w - 1))
        ry1 = int(clamp(y1 + 0.18 * bh, 0, img_h - 1))
        ry2 = int(clamp(y1 + 0.55 * bh, 0, img_h - 1))

        mask = np.zeros((img_h, img_w), dtype=np.uint8)
        cx = (rx1 + rx2) // 2
        cy = (ry1 + ry2) // 2
        ax = max(1, (rx2 - rx1) // 2)
        ay = max(1, (ry2 - ry1) // 2)
        cv2.ellipse(mask, (cx, cy), (ax, ay), 0, 0, 360, 255, -1)

        # bbox 기반 ROI는 거칠어서 dilation으로 버퍼를 더 주어 성능 보존
        k = max(3, int(self.cfg.bbox_fallback_dilate_px) // 2 * 2 + 1)
        kernel = np.ones((k, k), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

        # for debug
        rect = np.array(
            [[rx1, ry1], [rx2, ry1], [rx2, ry2], [rx1, ry2]], dtype=np.int32
        )
        return rect, mask, "bbox_fallback"
