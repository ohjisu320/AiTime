from app.rtn.types import MaskU8
from app.rtn.utils import clamp


def contact_by_raycast(
    eye_mask: MaskU8,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    n_samples: int = 11,
) -> bool:
    """
    시선 벡터(start_xy -> end_xy)가 부모 eye ROI(eye_mask)를 통과하는지 판정

    판정 방식(2D raycast 샘플링):
    - start -> end 선분을 n_samples개 점으로 동일 간격 샘플링
    - 샘플 중 하나라도 eye_mask(>0)에 닿으면 contact=True

    계약/좌표계:
    - eye_mask는 원본 프레임 좌표계 기준의 uint8 마스크(ROI=255).
    - start_xy/end_xy도 동일한 좌표계(픽셀)여야 함
      (좌표계가 다르면 항상 False/오작동 가능)

    튜닝 포인트:
    - n_samples가 클수록 얇은 ROI도 잡기 쉬워 안정적이지만 연산량이 증가
    - 너무 작으면(예: 2~3) ROI를 건너뛰는 미탐(FN)이 늘 수 있음

    한계:
    - 실제 3D 시선이 아니라 2D 투영 기반이므로, head pose/깊이 변화에는 오차 존재
    """
    h, w = eye_mask.shape[:2]
    sx, sy = start_xy
    ex, ey = end_xy

    if n_samples < 2:
        n_samples = 2

    for i in range(n_samples):
        t = i / (n_samples - 1)
        x = int(clamp(sx + (ex - sx) * t, 0, w - 1))
        y = int(clamp(sy + (ey - sy) * t, 0, h - 1))
        if eye_mask[y, x] > 0:
            return True
    return False
