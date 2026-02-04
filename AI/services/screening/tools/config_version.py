import argparse
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/preflight.yaml")
    ap.add_argument("--out", default="configs/preflight.version")
    ap.add_argument("--write", action="store_true", help="write hash to out file")
    args = ap.parse_args()

    cfg = Path(args.config)
    out = Path(args.out)

    if not cfg.exists():
        print(f"Error: {cfg} not found.")
        return

    h = sha256_file(cfg)

    print(h)
    if args.write:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(h + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

# python tools/config_version.py --write
