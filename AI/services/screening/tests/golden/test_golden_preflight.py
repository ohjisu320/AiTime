from pathlib import Path

import pytest
import yaml
from tools.replay_preflight import replay

ROOT = Path(__file__).resolve().parents[2]


def test_config_version_file_exists() -> None:
    p = ROOT / "configs" / "preflight.version"
    assert p.exists(), (
        "configs/preflight.version is missing. \
            Run: python tools/config_version.py --write"
    )


def test_golden_manifest() -> None:
    manifest_path = ROOT / "tests" / "golden" / "manifest.yaml"
    assert manifest_path.exists(), f"manifest not found: {manifest_path}"

    m = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    config_path = str(ROOT / m.get("config", "configs/preflight.yaml"))
    cfg_ver_path = ROOT / "configs" / "preflight.version"
    assert cfg_ver_path.exists(), "version file missing"
    cfg_ver = cfg_ver_path.read_text(encoding="utf-8").strip()

    assets_dir = ROOT / "tests" / "golden" / "assets"

    # If assets_dir doesn't exist, we might want to skip or fail with helpful message
    if not assets_dir.exists():
        pytest.skip("tests/golden/assets directory missing. Please provide mp4 assets.")

    for c in m["cases"]:
        mp4 = assets_dir / c["asset"]
        if not mp4.exists():
            # Instead of failing the whole test,
            # we can log and continue or fail specifically for this case
            # But in a regression test, missing asset usually means failure or skip.
            pytest.fail(f"missing asset: {mp4}")

        res = replay(mp4, config_path, cfg_ver)

        assert res["passed"] == c["expect_passed"], (
            f"{c['name']} passed mismatch: {res}"
        )
        exp_fr = c.get("expect_failure_reason")

        got_fr = res.get("failure_reason")
        if exp_fr is None:
            assert got_fr in (None, "", "null"), (
                f"{c['name']} expected no failure_reason: {res}"
            )
        else:
            assert got_fr == exp_fr, f"{c['name']} failure_reason mismatch: {res}"
