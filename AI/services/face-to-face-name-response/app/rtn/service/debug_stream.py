import time
from collections.abc import Iterator

import cv2
import numpy as np
from app.rtn.debug.broker import FrameBroker
from fastapi import APIRouter
from starlette.responses import StreamingResponse


def create_debug_router(broker: FrameBroker) -> APIRouter:
    """
    디버그 MJPEG 스트림 라우터를 생성
    just for develop mode and debug mode
    """
    router = APIRouter(prefix="/debug", tags=["debug"])

    @router.get("/mjpeg")
    def mjpeg() -> StreamingResponse:
        # multipart/x-mixed-replace에서 각 파트를 구분하는 boundary 문자열
        boundary = "frame"

        def gen() -> Iterator[bytes]:
            # 초기 프레임 없을 때 무한로딩 방지용 더미 프레임
            dummy = np.zeros((360, 640, 3), dtype=np.uint8)
            ok, buf = cv2.imencode(".jpg", dummy, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            dummy_jpeg = bytes(buf.tobytes()) if ok else b""

            last_ts = 0.0
            while True:
                jpeg, ts = broker.get_latest_jpeg()

                # 새 프레임이 없으면 keep-alive로 dummy를 가끔 보냄
                if jpeg is None:
                    payload = dummy_jpeg
                    time.sleep(0.1)
                else:
                    # ts는 broker가 관리하는 "마지막 프레임 갱신 시각"
                    # 같은 프레임 반복 과다 전송 방지(클라 부하 줄임)
                    if ts == last_ts:
                        time.sleep(0.01)
                        continue
                    last_ts = ts
                    payload = jpeg

                yield (
                    (
                        f"--{boundary}\r\n"
                        "Content-Type: image/jpeg\r\n"
                        f"Content-Length: {len(payload)}\r\n\r\n"
                    ).encode()
                    + payload
                    + b"\r\n"
                )

        return StreamingResponse(
            gen(),
            media_type=f"multipart/x-mixed-replace; boundary={boundary}",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    return router
