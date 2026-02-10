import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter()


def _quantile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    idx = int((len(xs) - 1) * q)
    return float(xs[idx])


@router.get("/stats/failure-reasons")
def failure_reasons(
    logs_dir: str = Query(default="artifacts/preflight/logs"),
    max_files: int = Query(default=200, ge=1, le=5000),
) -> dict[str, Any]:
    p = Path(logs_dir)
    if not p.exists():
        return {
            "logs_dir": logs_dir,
            "total_runs": 0,
            "passed": 0,
            "failed": 0,
            "by_reason": {},
        }

    files = sorted(p.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)[
        :max_files
    ]

    passed = 0
    failed = 0
    by_reason: dict[str, int] = {}

    for f in files:
        # 각 run 파일에서 result 이벤트 1개만 집계
        result = None
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("event") == "result":
                    result = obj
        except Exception:
            continue

        if not result:
            continue
        if result.get("passed") is True:
            passed += 1
        else:
            failed += 1
            r = result.get("failure_reason") or "UNKNOWN"
            by_reason[r] = by_reason.get(r, 0) + 1

    return {
        "logs_dir": logs_dir,
        "total_runs": passed + failed,
        "passed": passed,
        "failed": failed,
        "by_reason": by_reason,
    }


@router.get("/stats/stage-latency")
def stage_latency(
    logs_dir: str = Query(default="artifacts/preflight/logs"),
    max_files: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    p = Path(logs_dir)
    if not p.exists():
        return {"logs_dir": logs_dir, "by_stage": {}}

    files = sorted(p.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)[
        :max_files
    ]

    by_stage: dict[str, list[float]] = {}

    for f in files:
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("event") != "stage":
                    continue
                name = obj.get("stage_name", "unknown")
                lat = obj.get("latency_ms")
                if isinstance(lat, (int, float)):
                    by_stage.setdefault(name, []).append(float(lat))
        except Exception:
            continue

    out = {}
    for name, xs in by_stage.items():
        out[name] = {
            "count": len(xs),
            "p50_ms": _quantile(xs, 0.50),
            "p95_ms": _quantile(xs, 0.95),
            "max_ms": max(xs) if xs else 0.0,
        }

    return {"logs_dir": logs_dir, "by_stage": out}
