#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
비대면 호명과제 로컬 디버그 영상 생성 테스트

전체 파이프라인(Audio + Vision)을 실행하고 디버그 시각화 영상을 생성합니다.

Usage:
    # 기본 실행 (시각화 + JSON 출력)
    python test/test_debug_video.py --video sample_video/name_calling.mp4 --name "은연"

    # 오디오 건너뛰기 (Vision만 테스트, pyannote 없이)
    python test/test_debug_video.py --video sample_video/name_calling.mp4 --name "은연" --skip-audio

    # FPS 지정 + 프레임 이미지 저장
    python test/test_debug_video.py --video sample_video/name_calling.mp4 --name "은연" --fps 5 --save-frames

    # YOLO 디버그만 (파이프라인 없이 머리 탐지만)
    python test/test_debug_video.py --video sample_video/name_calling.mp4 --name "은연" --yolo-only

    # 결과 JSON 저장
    python test/test_debug_video.py --video sample_video/name_calling.mp4 --name "은연" -o output/result.json
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """로깅 설정"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


# ============================================================
# 모드 1: 전체 파이프라인 + 시각화
# ============================================================
def run_full_pipeline(args):
    """전체 파이프라인 실행 + 디버그 시각화 영상 생성"""
    from app.pipeline.orchestrator import FullPipelineOrchestrator
    from app.utils.visualize import create_visualization_video

    logger.info("=" * 60)
    logger.info("🧪 비대면 호명과제 디버그 영상 생성")
    logger.info("=" * 60)
    logger.info(f"   비디오: {args.video}")
    logger.info(f"   아이 이름: {args.name}")
    logger.info(f"   별명: {args.nickname or '없음'}")
    logger.info(f"   FPS: {args.fps or '기본값'}")
    logger.info(f"   오디오 건너뛰기: {args.skip_audio}")
    logger.info("=" * 60)

    # 파이프라인 실행 (continue_on_error: 개별 Stage 실패해도 계속 진행)
    start_time = time.time()
    orchestrator = FullPipelineOrchestrator(
        target_fps=args.fps,
        skip_audio=args.skip_audio,
        continue_on_error=True,
    )

    result = orchestrator.run(
        video_path=str(args.video),
        child_name=args.name,
        child_nickname=args.nickname,
    )
    elapsed = time.time() - start_time

    # Context 가져오기
    context = orchestrator.context

    # ===== Trial 결과 출력 =====
    print_trial_results(result)

    # ===== 처리 시간 출력 =====
    logger.info("\n⏱️ 처리 시간:")
    if context and context.processing_times:
        for stage, t in context.processing_times.items():
            logger.info(f"   {stage}: {t:.2f}s")
    logger.info(f"   ──────────────────")
    logger.info(f"   총 소요: {elapsed:.2f}s")

    # ===== 시각화 영상 생성 =====
    if context and context.frames:
        viz_output = args.viz_output
        logger.info(f"\n🎬 시각화 영상 생성 중...")

        output_path = create_visualization_video(
            context=context,
            output_path=viz_output,
            save_frames=args.save_frames,
        )
        logger.info(f"✅ 시각화 영상 저장: {output_path}")
    else:
        logger.warning("⚠️ 프레임 데이터 없음, 시각화 건너뜀")

    # ===== JSON 저장 =====
    if args.output:
        save_result_json(result, args.output)

    return result


# ============================================================
# 모드 2: YOLO 머리 탐지 디버그만
# ============================================================
def run_yolo_debug(args):
    """YOLO 머리 탐지만 실행하여 디버그 영상 생성"""
    from app.models.head_detector import HeadDetector

    logger.info("=" * 60)
    logger.info("🔍 YOLO 머리 탐지 디버그")
    logger.info("=" * 60)
    logger.info(f"   비디오: {args.video}")
    logger.info(f"   모델: {args.model or '기본값 (config)'}")
    logger.info("=" * 60)

    # 비디오 열기
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        logger.error(f"비디오를 열 수 없습니다: {args.video}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 타겟 FPS 계산
    target_fps = args.fps or 10
    frame_interval = max(1, int(fps / target_fps))

    logger.info(f"   원본: {width}x{height} @ {fps:.1f}fps, {total_frames}프레임")
    logger.info(f"   샘플링: 매 {frame_interval}프레임 ({target_fps}fps)")

    # 모델 로드 (싱글톤 패턴: __init__ 인자 대신 속성 직접 설정)
    detector = HeadDetector()
    if args.model:
        # 모델 경로가 상대경로면 프로젝트 루트 기준으로 변환
        model_path = Path(args.model)
        if not model_path.is_absolute():
            model_path = project_root / model_path
        detector._model_path = str(model_path)
        detector._model_loaded = False  # 커스텀 모델 사용 시 재로드
    else:
        # config의 기본 모델 경로도 절대 경로로 변환
        default_path = Path(detector._model_path)
        if not default_path.is_absolute():
            detector._model_path = str(project_root / default_path)
    detector.ensure_loaded()

    # 출력 영상
    output_path = Path(args.viz_output).with_name("yolo_debug.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, target_fps, (width, height))

    frame_idx = 0
    processed = 0
    total_detections = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            # 머리 탐지
            detections = detector.detect(frame)
            total_detections += len(detections)

            # 부모/아이 구분
            if args.selfie:
                # 셀피 모드: 부모 미탐지 허용 (기존 로직)
                parent_pos, child_det, parent_det = detector.identify_parent_child(
                    detections, frame.shape
                )
            else:
                # 2인 모드: 부모 반드시 탐지 시도
                if len(detections) >= 2:
                    # 2명 이상이면 부모/아이 구분
                    parent_pos, child_det, parent_det = detector.identify_parent_child(
                        detections, frame.shape
                    )
                elif len(detections) == 1:
                    # 1명만 탐지되면 아이로 가정, 부모는 화면 중앙
                    child_det = detections[0]
                    child_det.person_type = "child"
                    parent_det = None
                    parent_pos = (width / 2, height / 2)
                else:
                    # 0명이면 둘 다 None
                    parent_pos = (width / 2, height / 2)
                    child_det = None
                    parent_det = None

            # 시각화
            vis_frame = draw_yolo_debug_frame(
                frame, detections, parent_pos, child_det, parent_det, frame_idx
            )
            out.write(vis_frame)
            processed += 1

        frame_idx += 1

    cap.release()
    out.release()

    avg_det = total_detections / max(processed, 1)
    logger.info(f"\n✅ YOLO 디버그 영상 생성 완료")
    logger.info(f"   처리 프레임: {processed}")
    logger.info(f"   평균 탐지 수: {avg_det:.1f}")
    logger.info(f"   저장: {output_path}")


def draw_yolo_debug_frame(frame, detections, parent_pos, child_det, parent_det, frame_idx):
    """YOLO 탐지 결과를 프레임에 그리기"""
    vis = frame.copy()
    h, w = vis.shape[:2]

    # 프레임 정보
    cv2.putText(
        vis,
        f"Frame: {frame_idx} | Heads: {len(detections)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    for det in detections:
        x1, y1, x2, y2 = det.bbox.to_xyxy_pixel(w, h)
        cx, cy = det.bbox.center_pixel(w, h)

        # 신뢰도별 색상
        if det.confidence >= 0.7:
            color = (0, 255, 0)  # 초록
        elif det.confidence >= 0.5:
            color = (0, 255, 255)  # 노랑
        else:
            color = (0, 165, 255)  # 주황

        # 부모/아이 표시
        if child_det and det is child_det:
            color = (255, 0, 0)  # 파랑 = 아이
            label = f"Child #{det.confidence:.2f}"
        elif parent_det and det is parent_det:
            color = (0, 255, 0)  # 초록 = 부모
            label = f"Parent #{det.confidence:.2f}"
        else:
            label = f"#{det.confidence:.2f}"

        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
        cv2.circle(vis, (int(cx), int(cy)), 5, color, -1)

        # 라벨
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(vis, (x1, y1 - th - 10), (x1 + tw, y1), color, -1)
        cv2.putText(
            vis, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1
        )

    # 부모 중심 표시
    if parent_pos:
        px, py = int(parent_pos[0]), int(parent_pos[1])
        cv2.drawMarker(vis, (px, py), (0, 255, 0), cv2.MARKER_CROSS, 30, 2)

    return vis


# ============================================================
# 공통 유틸리티
# ============================================================
def print_trial_results(result):
    """Trial 결과 보기 좋게 출력"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 분석 결과")
    logger.info("=" * 60)

    if "trials" in result:
        for trial in result["trials"]:
            idx = trial.get("trial_index", "?")
            success = trial.get("success", False)
            latency = trial.get("latency_s")
            gaze = trial.get("gaze_match", False)
            voice = trial.get("voice_detected", False)

            icon = "✅" if success else "❌"
            latency_str = f"{latency:.2f}s" if latency else "N/A"

            logger.info(f"   [{idx}] {icon} latency={latency_str} gaze={'O' if gaze else 'X'} voice={'O' if voice else 'X'}")

            if trial.get("trigger_text"):
                logger.info(f"       호명: \"{trial['trigger_text']}\"")

    # ADOS 점수
    ados = result.get("ADOS", {})
    logger.info(f"\n   ADOS B7: {ados.get('B7', 'N/A')}")
    logger.info(f"   ADOS B18: {ados.get('B18', 'N/A')}")
    logger.info("=" * 60)


def save_result_json(result, output_path):
    """결과 JSON 파일 저장"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"📁 결과 JSON 저장: {path}")


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="비대면 호명과제 로컬 디버그 영상 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 전체 파이프라인 + 시각화
  python test/test_debug_video.py --video sample_video/name_calling.mp4 --name "은연"

  # Vision만 (오디오 건너뛰기)
  python test/test_debug_video.py --video sample_video/name_calling.mp4 --name "은연" --skip-audio

  # YOLO 머리 탐지만
  python test/test_debug_video.py --video sample_video/name_calling.mp4 --name "은연" --yolo-only

  # YouTube 영상 테스트
  python test/test_debug_video.py --video sample_video/name_calling_youtube_videos/video_1_11.mp4 --name "아기"
        """,
    )
    parser.add_argument("--video", "-v", type=str, required=True, help="비디오 파일 경로")
    parser.add_argument("--name", "-n", type=str, required=True, help="아이 이름")
    parser.add_argument("--nickname", type=str, default=None, help="아이 별명")
    parser.add_argument("--fps", type=int, default=None, help="프레임 추출 FPS (0=원본, None=config 기본값)")
    parser.add_argument("--skip-audio", action="store_true", help="오디오 분석 건너뛰기 (pyannote 미설치 시)")
    parser.add_argument("--yolo-only", action="store_true", help="YOLO 머리 탐지만 실행 (파이프라인 없이)")
    parser.add_argument("--selfie", action="store_true", help="셀피 모드 (1인칭, 부모 미탐지 허용). 기본값은 2인 모드(부모+아이)")
    parser.add_argument("--model", type=str, default=None, help="YOLO 모델 경로 (--yolo-only 시)")
    parser.add_argument("--output", "-o", type=str, default=None, help="결과 JSON 저장 경로")
    parser.add_argument("--viz-output", type=str, default="output/debug_visualization.mp4", help="시각화 영상 출력 경로")
    parser.add_argument("--save-frames", action="store_true", help="시각화 프레임 이미지 개별 저장")
    parser.add_argument("--debug", action="store_true", help="디버그 로깅")

    args = parser.parse_args()

    # 로깅 설정
    setup_logging(args.debug)

    # 비디오 파일 확인
    args.video = Path(args.video)
    if not args.video.exists():
        logger.error(f"비디오 파일이 존재하지 않습니다: {args.video}")
        sys.exit(1)

    # 실행 모드 선택
    if args.yolo_only:
        run_yolo_debug(args)
    else:
        run_full_pipeline(args)


if __name__ == "__main__":
    main()
