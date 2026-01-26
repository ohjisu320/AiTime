import numpy as np

from app.rtn.types import BBox, FrameBGR


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def iou_xyxy(a: BBox, b: BBox) -> float:
    """
    두 bbox의 IoU(Intersection over Union)를 계산

    입력/단위:
    - a, b는 (x1, y1, x2, y2) 픽셀 좌표(bbox corner)이며, x2>x1, y2>y1를 가정
    - 화면 밖 좌표가 들어와도 max(0, ...)로 안전하게 처리

    반환:
    - [0, 1] 범위의 float. 겹침이 없으면 0.0.
    """
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    iw = max(0.0, x2 - x1)
    ih = max(0.0, y2 - y1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, (a[2] - a[0])) * max(0.0, (a[3] - a[1]))
    area_b = max(0.0, (b[2] - b[0])) * max(0.0, (b[3] - b[1]))
    union = area_a + area_b - inter + 1e-9
    return float(inter / union)


def bbox_area_xyxy(b: BBox) -> float:
    return max(0.0, (b[2] - b[0])) * max(0.0, (b[3] - b[1]))


def smooth_xy(
    prev_xy: tuple[float, float] | None,
    cur_xy: tuple[float, float],
    alpha: float = 0.25,
    max_jump: float = 0.12,
) -> tuple[float, float]:
    """
    (x,y) 좌표를 1차 IIR(지수평활)로 부드럽게 만든다.

    동작:
    1) 현재 값(cur_xy)이 이전 값(prev_xy)에서 너무 멀리 뛰면(max_jump) 변화량을 clamp
    2) 그 결과에 대해 지수평활(s = alpha*cur + (1-alpha)*prev)

    파라미터 의미:
    - alpha: 0에 가까울수록 더 부드럽지만 지연이 커짐(반응 느림)
    - max_jump: 프레임 간 최대 이동량 제한(스파이크/오검출로 인한 급격한 튐 방지)
    - max_jump의 단위는 좌표계(정규화 좌표면 0~1 기준, 픽셀이면 픽셀 기준)
    """
    cx, cy = cur_xy
    if prev_xy is None:
        return (float(cx), float(cy))
    px, py = prev_xy
    cx = px + float(np.clip(cx - px, -max_jump, +max_jump))
    cy = py + float(np.clip(cy - py, -max_jump, +max_jump))
    sx = alpha * cx + (1 - alpha) * px
    sy = alpha * cy + (1 - alpha) * py
    return (float(sx), float(sy))


def crop_face_square(
    frame_bgr: FrameBGR,
    bbox_xyxy: BBox,
    margin: float = 0.35,
) -> tuple[FrameBGR, tuple[int, int]]:
    """
    bbox 중심을 기준으로 정사각형 crop을 만든다.

    입력/출력:
    - 입력 frame_bgr: OpenCV BGR 이미지(H,W,3)
    - bbox_xyxy: (x1,y1,x2,y2) 픽셀 좌표
    - 반환: (crop 이미지, (offset_x, offset_y))
      * offset은 crop의 좌상단이 원본 frame에서 시작한 좌표로,
        crop 내부 좌표를 원본 좌표로 되돌릴 때 사용

    동작:
    - bbox의 (폭,높이) 중 큰 값을 side로 하고, margin을 적용
        그래야 더 잘 적용됨
    - 영상 경계를 벗어나지 않도록 clamp
    """
    h, w = frame_bgr.shape[:2]
    x1, y1, x2, y2 = bbox_xyxy
    bw = x2 - x1
    bh = y2 - y1

    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0

    side = max(bw, bh) * (1.0 + 2.0 * margin)
    side = max(2.0, side)

    cx1 = int(clamp(cx - side / 2.0, 0, w - 1))
    cy1 = int(clamp(cy - side / 2.0, 0, h - 1))
    cx2 = int(clamp(cx + side / 2.0, 0, w - 1))
    cy2 = int(clamp(cy + side / 2.0, 0, h - 1))

    crop = frame_bgr[cy1:cy2, cx1:cx2].copy()
    return crop, (cx1, cy1)
