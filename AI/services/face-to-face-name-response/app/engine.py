import os
import threading

from .debug_stream import hub
from .face_to_face_name_response import VideoAnalyzer, analyze_video, build_analyzer

_ANALYZER: VideoAnalyzer | None = None
_LOCK = threading.Lock()  # ✅ mediapipe는 멀티스레드 동시 호출에 약해서 락 추천


def get_analyzer() -> VideoAnalyzer:
    global _ANALYZER
    if _ANALYZER is None:
        # 서버 시작 시 1회 생성
        _ANALYZER = build_analyzer(
            window_s=float(os.getenv("RTN_WINDOW_S", "5.0")),
            conf=float(os.getenv("RTN_FACE_CONF", "0.6")),
            debug=False,
            # debug=os.getenv("RTN_DEBUG", "0") == "1",
        )
        _ANALYZER.window_analyzer.debug_publish = hub.publish
    return _ANALYZER


def run_analyze(video_path: str) -> dict:
    analyzer = get_analyzer()
    # mediapipe/torch 객체를 공유하는 경우 안정성을 위해 락
    with _LOCK:
        return analyze_video(video_path, analyzer)
