import hashlib
from pathlib import Path


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_preflight_config_version_matches() -> None:
    # Use paths relative to current directory if run from screening service root
    cfg = Path("configs/preflight.yaml")
    ver = Path("configs/preflight.version")

    # If not found, try relative to tests dir
    if not cfg.exists():
        root = Path(__file__).resolve().parents[1]
        cfg = root / "configs" / "preflight.yaml"
        ver = root / "configs" / "preflight.version"

    assert cfg.exists(), f"config file not found: {cfg.absolute()}"
    assert ver.exists(), (
        "missing configs/preflight.version. Run: python tools/config_version.py --write"
    )

    want = sha256_file(cfg)
    got = ver.read_text(encoding="utf-8").strip()
    assert got == want, (
        f"config_version mismatch."
        f"\nwant={want}\ngot={got}\nRun: python tools/config_version.py --write"
    )
