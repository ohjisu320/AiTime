import threading

import cv2
import numpy as np
import numpy.typing as npt


class DebugFrameHub:
    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._jpg = None

    def publish(self, frame_bgr: npt.NDArray[np.uint8]) -> None:
        ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            return
        jpg = buf.tobytes()
        with self._cond:
            self._jpg = jpg
            self._cond.notify_all()

    def get(self, timeout: float = 1.0) -> bytes | None:
        with self._cond:
            if self._jpg is None:
                self._cond.wait(timeout)
            return self._jpg


hub = DebugFrameHub()
