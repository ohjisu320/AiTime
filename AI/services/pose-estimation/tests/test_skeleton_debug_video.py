"""
디버그 스켈레톤 영상 생성 테스트 스크립트.

sample_video/ 폴더의 영상들을 분석하고,
스켈레톤이 오버레이된 디버그 영상(.mp4)을 analysis_output/ 에 생성합니다.

[ 실행법 ]
  # pose-estimation 디렉토리에서 실행
  cd AI/services/pose-estimation

  # ── 단일 동작 모드 ──
  # 1) 전체 샘플 영상 일괄 처리
  python -m tests.test_skeleton_debug_video

  # 2) 특정 동작만
  python -m tests.test_skeleton_debug_video --action clapping

  # 3) 특정 영상 파일 지정
  python -m tests.test_skeleton_debug_video --video sample_video/pose_clapping_T.mp4 --action clapping

  # ── Multi-Trial 모드 (16초 구간 분할) ──
  # 4) 연속 영상을 16초씩 3구간으로 분할 분석 + 합본 영상 생성
  python -m tests.test_skeleton_debug_video --multi-trial --video 영상.mp4 --age 18

  # 5) 출력 폴더 변경 / 상세 로그
  python -m tests.test_skeleton_debug_video --multi-trial --video 영상.mp4 --age 15 -o my_output --verbose
"""

import argparse
import sys
import time
import logging
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.pipeline.analyzer import MotionAnalyzer
from app.worker import get_action_set_by_age

logger = logging.getLogger(__name__)

# =========================================================================
# 샘플 영상 <-> 동작 타입 매핑
# 파일명 규칙: pose_{action}_{T|F}.mp4  (T=통과, F=실패 기대)
# =========================================================================
SAMPLE_VIDEO_DIR = PROJECT_ROOT / "sample_video"

SAMPLE_MAP = {
    "pose_clapping_T.mp4":  "clapping",
    "pose_clapping_F.mp4":  "clapping",
    "pose_hurray_T.mp4":    "hurray",
    "pose_hurray_F.mp4":    "hurray",
    "pose_jumping_T.mp4":   "jumping",
    "pose_kicking_T.mp4":   "kicking",
    "pose_throwing_T.mp4":  "throwing",
    "pose_throwing_F.mp4":  "throwing",
}


# =========================================================================
# 단일 동작 모드
# =========================================================================
def run_single(
    video_path: Path,
    action_type: str,
    output_root: Path,
    age_months: int = 18,
    verbose: bool = False,
) -> dict:
    """단일 영상에 대해 스켈레톤 디버그 영상 생성."""

    output_folder = output_root / f"{video_path.stem}_{action_type}"
    output_folder.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  영상:   {video_path.name}")
    print(f"  동작:   {action_type}")
    print(f"  출력:   {output_folder}")
    print(f"{'='*60}")

    analyzer = MotionAnalyzer(use_folder_mode=True)

    t0 = time.time()
    result = analyzer.analyze_with_visualization(
        video_path=str(video_path),
        action_type=action_type,
        age_months=age_months,
        output_folder=str(output_folder),
        save_skeleton_video=True,
        use_parent_reference=True,
        identify_roles=True,
        smooth=True,
        smooth_method="one_euro",
    )
    elapsed = time.time() - t0

    # ── 결과 요약 출력 ──
    if result.details.get("fail_reason") == "child_action_not_detected":
        status = "FAIL (아이 동작 미감지)"
        score = "N/A"
    else:
        status = "PASS" if result.passed else "FAIL"
        score = f"{result.similarity_score:.2%}"

    print(f"  결과:       {status}")
    print(f"  유사도:     {score}")
    if result.reaction_delay_sec is not None:
        print(f"  반응 지연:  {result.reaction_delay_sec:.2f}s")
    if result.duration_sec is not None:
        print(f"  동작 지속:  {result.duration_sec:.2f}s")
    print(f"  처리 시간:  {elapsed:.1f}s")

    if result.visualization_info:
        skeleton_video = result.visualization_info.get("skeleton_video")
        if skeleton_video:
            print(f"  스켈레톤 영상: {skeleton_video}")
        print(f"  추출 프레임:   {result.visualization_info.get('extracted_frames', 0)}개")
        print(f"  시각화 프레임: {result.visualization_info.get('visualized_frames', 0)}개")

    return {
        "video": video_path.name,
        "action": action_type,
        "status": status,
        "score": score,
        "elapsed": elapsed,
        "skeleton_video": result.visualization_info.get("skeleton_video") if result.visualization_info else None,
    }


def run_all(
    output_root: Path,
    action_filter: str | None = None,
    verbose: bool = False,
):
    """sample_video/ 의 전체(또는 필터링된) 영상에 대해 일괄 처리."""
    results = []

    for filename, action in SAMPLE_MAP.items():
        if action_filter and action != action_filter:
            continue

        video_path = SAMPLE_VIDEO_DIR / filename
        if not video_path.exists():
            print(f"[SKIP] 파일 없음: {video_path}")
            continue

        try:
            r = run_single(video_path, action, output_root, verbose=verbose)
            results.append(r)
        except Exception as e:
            print(f"[ERROR] {filename}: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            results.append({
                "video": filename,
                "action": action,
                "status": f"ERROR: {e}",
                "score": "N/A",
                "elapsed": 0,
                "skeleton_video": None,
            })

    # ── 최종 요약 ──
    print(f"\n{'='*60}")
    print("  최종 요약")
    print(f"{'='*60}")
    for r in results:
        tag = "OK" if "PASS" in str(r["status"]) or "FAIL" in str(r["status"]) else "ERR"
        print(f"  [{tag}] {r['video']:30s}  {r['status']:20s}  유사도={r['score']}  ({r['elapsed']:.1f}s)")

    skeleton_count = sum(1 for r in results if r.get("skeleton_video"))
    print(f"\n  생성된 스켈레톤 영상: {skeleton_count}/{len(results)}개")
    print(f"  출력 위치: {output_root.resolve()}")
    print(f"{'='*60}\n")


# =========================================================================
# Multi-Trial 모드 (16초 구간 분할 + 합본)
# =========================================================================
def run_multi_trial(
    video_path: Path,
    age_months: int,
    output_root: Path,
    verbose: bool = False,
):
    """연속 영상을 16초씩 3구간으로 분할 분석 + 합본 영상 생성."""

    action_list = get_action_set_by_age(age_months)

    print(f"\n{'='*60}")
    print("  Multi-Trial 시각화 분석")
    print(f"{'='*60}")
    print(f"  영상:     {video_path.name}")
    print(f"  월령:     {age_months}개월")
    print(f"  동작:     {' → '.join(action_list)}")
    print(f"  구간:     0~16s / 16~32s / 32~48s")
    print(f"  출력:     {output_root}")
    print(f"{'='*60}")

    analyzer = MotionAnalyzer(use_folder_mode=True)

    t0 = time.time()
    result = analyzer.analyze_multi_trial_with_visualization(
        video_path=str(video_path),
        action_list=action_list,
        age_months=age_months,
        output_folder=str(output_root),
        identify_roles=True,
        smooth=True,
        smooth_method="one_euro",
    )
    elapsed = time.time() - t0

    # ── trial별 결과 ──
    print(f"\n{'='*60}")
    print("  Trial 결과")
    print(f"{'='*60}")
    for t in result.metrics["per_trial"]:
        status = "PASS" if t["success"] else "FAIL"
        score = f"{t['similarity_score']:.2%}"
        latency = (
            f"{t['latency_s']:.2f}s"
            if t.get("latency_s") is not None
            else "N/A"
        )
        print(
            f"  Trial {t['trial_index']}: {t['action_type']:15s}"
            f"  {status}  유사도={score}  반응지연={latency}"
        )

    # ── ADOS 점수 ──
    print(f"\n  ADOS 점수:")
    print(f"    A8  (주의/반응):  {result.ados['A8']}")
    print(f"    B6  (즐거움):    {result.ados['B6']}")
    print(f"    B18 (사회적 상호작용):  {result.ados['B18']}")

    # ── 영상 경로 ──
    viz = result.details.get("visualization", {})
    merged = viz.get("merged_video")
    print(f"\n  처리 시간: {elapsed:.1f}s")
    if merged:
        print(f"  합본 영상: {merged}")
    trial_videos = viz.get("trial_videos", [])
    for i, tv in enumerate(trial_videos, 1):
        if tv:
            print(f"  Trial {i} 영상: {tv}")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="디버그 스켈레톤 영상 생성 테스트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 단일 동작
  python -m tests.test_skeleton_debug_video
  python -m tests.test_skeleton_debug_video --action clapping
  python -m tests.test_skeleton_debug_video --video sample_video/pose_hurray_T.mp4 --action hurray

  # Multi-Trial (16초 구간 분할)
  python -m tests.test_skeleton_debug_video --multi-trial --video 영상.mp4 --age 18
  python -m tests.test_skeleton_debug_video --multi-trial --video 영상.mp4 --age 15 --verbose
        """,
    )
    parser.add_argument(
        "--video",
        help="특정 영상 파일 경로 (미지정 시 sample_video/ 전체)",
    )
    parser.add_argument(
        "--action",
        choices=MotionAnalyzer.SUPPORTED_ACTIONS,
        help="동작 타입 (--video 사용 시 필수, 미지정 시 전체)",
    )
    parser.add_argument(
        "--age",
        type=int,
        default=18,
        help="아동 월령 (기본: 18)",
    )
    parser.add_argument(
        "--output", "-o",
        default="analysis_output",
        help="출력 루트 폴더 (기본: analysis_output)",
    )
    parser.add_argument(
        "--multi-trial",
        action="store_true",
        help="Multi-Trial 모드: 16초씩 3구간 분할 분석 + 합본 영상",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)

    if args.multi_trial:
        # ── Multi-Trial 모드 ──
        if not args.video:
            print("--multi-trial 사용 시 --video 를 지정해야 합니다.")
            sys.exit(1)
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"영상 파일을 찾을 수 없습니다: {video_path}")
            sys.exit(1)
        run_multi_trial(video_path, args.age, output_root, args.verbose)

    elif args.video:
        # ── 특정 영상 단일 분석 ──
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"영상 파일을 찾을 수 없습니다: {video_path}")
            sys.exit(1)
        if not args.action:
            print("--video 사용 시 --action 도 지정해야 합니다.")
            sys.exit(1)
        run_single(video_path, args.action, output_root, args.age, args.verbose)

    else:
        # ── 전체 일괄 모드 ──
        run_all(output_root, action_filter=args.action, verbose=args.verbose)


if __name__ == "__main__":
    main()
