from app.rtn.types import Track
from app.rtn.utils import bbox_area_xyxy


class RoleAssignerByArea:
    """
    warmup 구간에서 track별 평균 얼굴 면적을 누적해,
    큰 얼굴 = parent, 작은 얼굴 = child 로 지정
    """

    def __init__(self, warmup_s: float) -> None:
        self.warmup_s = warmup_s
        self.stats: dict[int, dict[str, float]] = {}
        self.assigned: bool = False
        self.parent_id: int | None = None
        self.child_id: int | None = None

    def update_warmup(self, cur_t: float, start_t: float, tracks: list[Track]) -> None:
        if cur_t <= start_t + self.warmup_s:
            for x1, y1, x2, y2, tid in tracks:
                area = bbox_area_xyxy((x1, y1, x2, y2))
                st = self.stats.setdefault(tid, {"sum_area": 0.0, "cnt": 0.0})
                st["sum_area"] += area
                st["cnt"] += 1.0

    def maybe_assign(self, cur_t: float, start_t: float) -> None:
        if self.assigned:
            return
        if cur_t < start_t + self.warmup_s:
            return
        if len(self.stats) < 2:
            return

        items: list[tuple[float, float, int]] = []
        for tid, st in self.stats.items():
            if st["cnt"] <= 0:
                continue
            mean_area = st["sum_area"] / st["cnt"]
            items.append((st["cnt"], mean_area, tid))
        items.sort(reverse=True)

        top2 = items[:2]
        if len(top2) != 2:
            return

        if top2[0][1] >= top2[1][1]:
            self.parent_id = top2[0][2]
            self.child_id = top2[1][2]
        else:
            self.parent_id = top2[1][2]
            self.child_id = top2[0][2]

        self.assigned = True
