"""Listen for LiveKit data messages in a room and print them.

Useful if you don't want to open the browser client.
Requires a token (use gen_tokens.py first).

Example:
  python tools/data_listener.py --tokens artifacts/smoke/tokens.json
"""

import argparse
import asyncio
import json
from pathlib import Path

from livekit import rtc


async def main_async(tokens_path: str) -> None:
    tokens = json.loads(Path(tokens_path).read_text(encoding="utf-8"))
    room_name = tokens["room"]
    url = tokens.get("livekit_url", "ws://localhost:7880")
    token = tokens["user_token"]

    room = rtc.Room()

    @room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket) -> None:
        try:
            txt = data_packet.data.decode("utf-8", errors="replace")
        except Exception:
            txt = str(data_packet.data)
        ident = getattr(data_packet.participant, "identity", None)
        print(
            f"[data_listener] from={ident} topic={data_packet.topic} "
            f"reliable={data_packet.reliable} :: {txt}"
        )

    print(f"[data_listener] connecting to room={room_name} url={url}")
    await room.connect(url, token)
    print("[data_listener] connected; waiting...")
    # Wait forever (Ctrl+C to stop)
    while True:
        await asyncio.sleep(3600)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--tokens", default="artifacts/smoke/tokens.json")
    args = p.parse_args()
    asyncio.run(main_async(args.tokens))


if __name__ == "__main__":
    main()
