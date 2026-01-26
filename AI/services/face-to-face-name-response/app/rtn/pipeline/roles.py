from app.rtn.types import Track
from app.rtn.utils import bbox_area_xyxy


class RoleAssignerByArea:
    """
    warmup 구간에서 track별 평균 얼굴 bbox 면적을 누적해 역할을 할당
    - 큰 얼굴(평균 면적 크면) = parent
    - 작은 얼굴(평균 면적 작으면) = child

    가정/제한:
    - 부모가 카메라에 더 가깝게(더 크게) 잡힌다는 전제가 필요
    - 두 사람이 거리/각도 차이가 없거나, 아이가 더 가까우면 오할당될 수 있음
    - track ID가 warmup 동안 안정적으로 유지되어야 함(SORT ID switch에 취약)
        그래서 적용이 track 이후에 들어가야 하는 것

    운영 팁:
    - 실패가 잦으면 area 외에 위치(좌/우), 높이(y), 얼굴 landmark 기반 head size 등을
      함께 써서 보완 가능
    """

    def __init__(self, warmup_s: float) -> None:
        self.warmup_s = warmup_s
        self.stats: dict[int, dict[str, float]] = {}
        self.assigned: bool = False
        self.parent_id: int | None = None
        self.child_id: int | None = None

    def update_warmup(self, cur_t: float, start_t: float, tracks: list[Track]) -> None:
        # warmup 구간에만 통계를 누적해 초기 프레임의 흔들림을 평균으로 상쇄
        # stats[tid] = {"sum_area": 누적 면적, "cnt": 샘플 수}
        if cur_t <= start_t + self.warmup_s:
            for x1, y1, x2, y2, tid in tracks:
                area = bbox_area_xyxy((x1, y1, x2, y2))
                st = self.stats.setdefault(tid, {"sum_area": 0.0, "cnt": 0.0})
                st["sum_area"] += area
                st["cnt"] += 1.0

    def maybe_assign(self, cur_t: float, start_t: float) -> None:
        # 재할당하지 않음
        if self.assigned:
            return
        # warmup 기다림
        if cur_t < start_t + self.warmup_s:
            return
        # 인원 확인
        if len(self.stats) < 2:
            return

        # cnt(관측 수)가 많은 트랙을 우선 선택
        #   -> 더 안정적으로 관측된 두 트랙을 top2로 선정
        # 그 다음 mean_area로 parent/child를 결정
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
