import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가 (테스트 실행 용이성)
sys.path.append(str(Path(__file__).parents[2]))

from app.config import get_settings
from app.utils.repro import compute_config_hash


def test_config_hash() -> None:
    settings = get_settings()
    h1 = compute_config_hash(settings)
    assert len(h1) == 16

    # 두 번 호출해도 같아야 함 (Idempotency)
    h2 = compute_config_hash(settings)
    assert h1 == h2


if __name__ == "__main__":
    try:
        test_config_hash()
        print("✅ test_config_hash PASSED")
    except Exception as e:
        print(f"❌ test_config_hash FAILED: {e}")
        sys.exit(1)
