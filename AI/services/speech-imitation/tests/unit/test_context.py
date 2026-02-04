import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[2]))

from app.pipeline.context import PipelineContext


def test_context_observability() -> None:
    ctx = PipelineContext(request_id="test_req")

    # Metric 추가
    ctx.add_metric("Phase1", "acc", 0.95)
    ctx.add_metric("Phase1", "loss", 0.1)

    assert "Phase1" in ctx.stage_metrics
    assert ctx.stage_metrics["Phase1"]["acc"] == 0.95

    # Flag 추가
    ctx.add_flag("LOW_CONFIDENCE")
    ctx.add_flag("LOW_CONFIDENCE")  # 중복 추가 시도

    assert len(ctx.quality_flags) == 1
    assert "LOW_CONFIDENCE" in ctx.quality_flags


if __name__ == "__main__":
    try:
        test_context_observability()
        print("✅ test_context_observability PASSED")
    except Exception as e:
        print(f"❌ test_context_observability FAILED: {e}")
        sys.exit(1)
