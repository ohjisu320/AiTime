import threading
import time

import cv2
import numpy as np

from app.rtn.types import FrameBGR


class FrameBroker:
    """
    - 분석 루프에서 publish(bgr)을 계속 호출 → 최신 JPEG만 유지
    - /debug/mjpeg에서는 get_latest_jpeg()를 반복 호출하여 스트리밍
    """

    def __init__(self, jpeg_quality: int = 80) -> None:
        self._lock = threading.Lock()
        self._jpeg: bytes | None = None
        self._ts: float = 0.0
        self._q = int(np.clip(jpeg_quality, 30, 95))

    def publish(self, frame_bgr: FrameBGR) -> None:
        ok, buf = cv2.imencode(
            ".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), self._q]
        )
        if not ok:
            return
        data = bytes(buf.tobytes())
        with self._lock:
            self._jpeg = data
            self._ts = time.time()

    def get_latest_jpeg(self) -> tuple[bytes | None, float]:
        with self._lock:
            return self._jpeg, self._ts
