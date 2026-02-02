"""Generate LiveKit JWT tokens for local smoke testing.

- Designed for LiveKit dev server (API key/secret: devkey/secret)
- Writes a JSON containing room/url/identity + user/ai tokens

If you see DisconnectReason.DUPLICATE_IDENTITY (=2), it's usually because
multiple tabs (or reconnect) joined the same room with the same identity.
So defaults here make identities unique per room.
"""

import argparse
import datetime as dt
import json
import os
from pathlib import Path


def _load_livekit_api() -> object:
    # Token minting via LiveKit server SDK
    try:
        from livekit import api  # type: ignore

        return api
    except Exception as e:
        raise RuntimeError(
            "Failed to import `from livekit import api`.\n"
            "Try: pip install livekit-api\n"
            f"Original error: {e}"
        ) from e


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--room", required=True)
    p.add_argument(
        "--livekit-url", default=os.getenv("LIVEKIT_URL", "ws://127.0.0.1:7880")
    )
    p.add_argument("--api-key", default=os.getenv("LIVEKIT_API_KEY", "devkey"))
    p.add_argument("--api-secret", default=os.getenv("LIVEKIT_API_SECRET", "secret"))
    p.add_argument("--ttl-hours", type=float, default=2.0)

    p.add_argument("--user-identity", default=None)
    p.add_argument("--user-name", default="Smoke User")
    p.add_argument("--ai-identity", default=None)
    p.add_argument("--ai-name", default="Smoke AI")

    p.add_argument("--out", default="artifacts/smoke/tokens.json")
    args = p.parse_args()

    api = _load_livekit_api()

    ttl = dt.timedelta(seconds=int(args.ttl_hours * 3600))

    # Unique identities per room by default
    user_identity = args.user_identity or f"user-smoke-{args.room}"
    ai_identity = args.ai_identity or f"ai-smoke-{args.room}"

    def mk(identity: str, name: str) -> str:
        at = api.AccessToken(args.api_key, args.api_secret)
        at.with_identity(identity)
        at.with_name(name)
        at.with_ttl(ttl)
        at.with_grants(
            api.VideoGrants(
                room_join=True,
                room=args.room,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        return at.to_jwt()

    out = {
        "room": args.room,
        "livekit_url": args.livekit_url,
        "user_identity": user_identity,
        "ai_identity": ai_identity,
        "user_token": mk(user_identity, args.user_name),
        "ai_token": mk(ai_identity, args.ai_name),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[gen_tokens] wrote: {out_path.resolve()}")


if __name__ == "__main__":
    main()
