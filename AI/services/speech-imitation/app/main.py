"""
CLI 엔트리포인트

Usage:
    python -m app.main --video path/to.mp4 --age-months 18
"""

import argparse
import json

from app.pipeline.orchestrator import SpeechImitationPipelineOrchestrator


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="입력 비디오 경로")
    ap.add_argument("--age-months", type=int, required=True, help="아이 월령(12~23)")
    ap.add_argument("--request-id", default=None, help="요청 ID (옵션)")
    args = ap.parse_args()

    orch = SpeechImitationPipelineOrchestrator()
    result = orch.run(args.video, args.age_months, request_id=args.request_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
