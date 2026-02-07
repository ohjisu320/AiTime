"""
VisualizationStage
- 파이프라인 처리 결과를 비디오 위에 시각화하여 저장
- Pillow를 사용하여 한국어 폰트(맑은 고딕) 렌더링
- 일반인도 알기 쉬운 UI/UX 적용
"""

import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.config import get_settings
from app.models.speaker_splitter import SpeakerLabel
from app.pipeline.context import PipelineContext
from app.pipeline.stages.base_stage import BaseStage

logger = logging.getLogger(__name__)


class VisualizationStage(BaseStage):
    def __init__(self) -> None:
        self._settings = get_settings()

        # 폰트 로드: 프로젝트 내 assets/fonts 우선
        # 없으면 시스템 폰트(malgun), 실패 시 기본
        try:
            self.FONT_PATH = "assets/fonts/NanumGothic.ttf"
            if not Path(self.FONT_PATH).exists():
                logger.warning("로컬 폰트 없음, 시스템 폰트(맑은 고딕) 시도")
                self.FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

            self._font_header = ImageFont.truetype(self.FONT_PATH, 32)
            self._font_title = ImageFont.truetype(self.FONT_PATH, 24)
            self._font_text = ImageFont.truetype(self.FONT_PATH, 20)
            self._font_sub = ImageFont.truetype(self.FONT_PATH, 16)
            self._font_target = ImageFont.truetype(self.FONT_PATH, 50)  # 목표 단어 강조
        except Exception as e:
            logger.warning(f"폰트 로드 실패, 기본 폰트 사용: {e}")
            self._font_header = ImageFont.load_default()
            self._font_title = ImageFont.load_default()
            self._font_text = ImageFont.load_default()
            self._font_sub = ImageFont.load_default()
            self._font_target = ImageFont.load_default()

        # 색상 정의 (RGB)
        self.COLOR_BG = (40, 40, 45)  # 차분한 다크 그레이
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_GRAY_TEXT = (200, 200, 200)

        # 상태 색상 (파스텔 톤)
        self.COLOR_PARENT = (255, 180, 100)  # 살구색/오렌지 (엄마)
        self.COLOR_CHILD = (100, 220, 150)  # 민트/그린 (아기)

        # 판정 색상
        self.COLOR_SUCCESS = (80, 220, 100)  # 밝은 초록
        self.COLOR_FAIL = (255, 100, 100)  # 밝은 빨강
        self.COLOR_WARN = (255, 200, 50)  # 노랑/오렌지

        # UI 요소
        self.SIDEBAR_WIDTH = 500

    @property
    def name(self) -> str:
        return "VisualizationStage"

    def process(self, context: PipelineContext) -> None:
        if not context.video_path or not Path(context.video_path).exists():
            return

        p = Path(context.video_path)
        output_path = p.with_name(f"{p.stem}_debug_kr.mp4")

        cap = cv2.VideoCapture(context.video_path)
        if not cap.isOpened():
            return

        out = None
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            new_width = width + self.SIDEBAR_WIDTH

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (new_width, height))

            logger.info(f"한국어 시각화 비디오 생성 시작: {output_path}")

            current_frame = 0

            # --- Pre-calculation ---
            parent_segs = [
                (s.segment.start_sec, s.segment.end_sec)
                for s in context.labeled_segments
                if s.label == SpeakerLabel.ADULT
            ]
            child_segs = [
                (s.segment.start_sec, s.segment.end_sec)
                for s in context.labeled_segments
                if s.label == SpeakerLabel.CHILD
            ]

            timeline_events = []
            for t in context.trial_results:
                for r in t.repetitions:
                    if r.stimulus_time:
                        timeline_events.append(
                            {
                                "start": r.stimulus_time[0],
                                "end": r.stimulus_time[1],
                                "type": "STIMULUS",
                                "trial": t.trial_index,
                                "rep": r.rep_index,
                                "text": t.stimulus_text,
                            }
                        )
                    if r.response_time and r.response_detected:
                        timeline_events.append(
                            {
                                "start": r.response_time[0],
                                "end": r.response_time[1],
                                "type": "RESPONSE",
                                "trial": t.trial_index,
                                "rep": r.rep_index,
                                "info": r,
                                "text": t.stimulus_text,
                            }
                        )

            # Thresholds
            th_sim = self._settings.SIMILARITY_THRESHOLD
            th_pitch = self._settings.PITCH_SQUEAL_HZ_THRESHOLD
            th_mad_min = self._settings.PITCH_MAD_MONOTONE_THRESHOLD
            th_mad_max = self._settings.PITCH_MAD_SONG_THRESHOLD

            # 성공 횟수 계산용
            total_reps = sum(len(t.repetitions) for t in context.trial_results)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                timestamp = current_frame / fps

                # 1. Canvas Setup (OpenCV BGR -> PIL RGB)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 전체 캔버스 생성
                canvas = Image.new("RGB", (new_width, height), self.COLOR_BG)

                # 원본 영상 붙이기
                # PIL Image 객체로 변환
                img_frame = Image.fromarray(frame_rgb)
                canvas.paste(img_frame, (self.SIDEBAR_WIDTH, 0))

                draw = ImageDraw.Draw(canvas)

                # 2. Status Determination
                is_parent_speaking = any(s <= timestamp <= e for s, e in parent_segs)
                is_child_speaking = any(s <= timestamp <= e for s, e in child_segs)

                current_event = None
                for evt in timeline_events:
                    if evt["start"] <= timestamp <= evt["end"]:
                        current_event = evt
                        break

                # 최근 결과 찾기 (현재 시점보다 이전에 끝난 RESPONSE 중 가장 최신)
                last_response_event = None
                curr_success_count = 0

                # 누적 성공 횟수 계산 및 최근 결과 조회
                for evt in timeline_events:
                    if evt["type"] == "RESPONSE":
                        # 완료되었거나 현재 진행 중인 이벤트라면 카운트 (즉시 반영)
                        if evt["end"] < timestamp or (
                            current_event and current_event == evt
                        ):
                            info = evt["info"]
                            if info.success:
                                curr_success_count += 1

                        # 최근 완료된 결과 찾기 (진행중 제외, 완료 기준)
                        if evt["end"] < timestamp:
                            last_response_event = evt

                # 현재 보여줄 분석 결과 (진행중 혹은 완료된 RESPONSE)
                # 사용자 요청: "빈틈 채우기" -> 계속 유지
                target_evt = (
                    current_event
                    if (current_event and current_event["type"] == "RESPONSE")
                    else last_response_event
                )

                # 3. Rendering (Sidebar)
                x_margin = 30
                y = 40

                # --- [ HEADER ] ---
                draw.text(
                    (x_margin, y),
                    "AI 발화 분석",
                    font=self._font_header,
                    fill=self.COLOR_WHITE,
                )
                y += 50
                draw.text(
                    (x_margin, y),
                    f"진행 시간: {timestamp:.1f}초",
                    font=self._font_text,
                    fill=self.COLOR_GRAY_TEXT,
                )
                y += 60

                # --- [ SECTION 1: 현재 상태 ] ---
                # 상태 박스 그리기
                status_text = "대기 중..."
                status_color = (80, 80, 80)

                if current_event:
                    if current_event["type"] == "STIMULUS":
                        status_text = "엄마 말씀하시는 중"
                        status_color = self.COLOR_PARENT
                    elif current_event["type"] == "RESPONSE":
                        status_text = "아기 따라하는 중"
                        status_color = self.COLOR_CHILD
                elif is_parent_speaking:
                    status_text = "엄마 목소리 감지됨"
                    status_color = (200, 140, 80)  # 조금 어두운 오렌지
                elif is_child_speaking:
                    status_text = "아기 목소리 감지됨"
                    status_color = (80, 180, 120)  # 조금 어두운 그린

                # Rounded Box 느낌 (PIL rectangle)
                box_h = 60
                draw.rectangle(
                    [(x_margin, y), (self.SIDEBAR_WIDTH - x_margin, y + box_h)],
                    fill=status_color,
                )

                # 텍스트 중앙 정렬 계산
                bbox = draw.textbbox((0, 0), status_text, font=self._font_title)
                w_text = bbox[2] - bbox[0]
                h_text = bbox[3] - bbox[1]
                txt_x = x_margin + (self.SIDEBAR_WIDTH - 2 * x_margin - w_text) // 2
                txt_y = y + (box_h - h_text * 1.5) // 2  # 얼추 중앙

                draw.text(
                    (txt_x, txt_y),
                    status_text,
                    font=self._font_title,
                    fill=(30, 30, 30),
                )  # 검은 글씨
                y += 90

                # --- [ SECTION 2: 이번 목표 ] ---
                draw.text(
                    (x_margin, y),
                    "이번 목표 단어",
                    font=self._font_sub,
                    fill=self.COLOR_GRAY_TEXT,
                )
                y += 30

                target_word = "-"
                trial_info = "-"

                # 현재 혹은 다음 목표 찾기
                # 가장 가까운 미래의 STIMULUS 혹은 현재 진행중인 것
                active_trial_idx = -1

                if current_event:
                    target_word = f"'{current_event.get('text', '?')}'"
                    active_trial_idx = current_event["trial"]
                    trial_info = f"{current_event['rep']}번째 시도"
                else:
                    # 미래의 첫 Stimulus 찾기
                    found_future = False
                    for evt in timeline_events:
                        if evt["type"] == "STIMULUS" and evt["start"] > timestamp:
                            target_word = f"'{evt.get('text', '?')}'"
                            active_trial_idx = evt["trial"]
                            trial_info = "준비 중"
                            found_future = True
                            break
                    if not found_future and last_response_event:
                        # 모두 끝났으면 마지막 정보 유지
                        target_word = f"'{last_response_event.get('text', '?')}' (종료)"
                        active_trial_idx = last_response_event["trial"]
                        trial_info = "분석 완료"

                draw.text(
                    (x_margin + 10, y),
                    target_word,
                    font=self._font_target,
                    fill=self.COLOR_WHITE,
                )
                y += 70
                draw.text(
                    (x_margin, y),
                    f"상태: {trial_info} (Trial {active_trial_idx})",
                    font=self._font_text,
                    fill=self.COLOR_GRAY_TEXT,
                )
                y += 60

                # 구분선
                draw.line(
                    [(x_margin, y), (self.SIDEBAR_WIDTH - x_margin, y)],
                    fill=(100, 100, 100),
                    width=2,
                )
                y += 30

                # --- [ SECTION 3: 실시간 분석 (XAI) ] ---
                draw.text(
                    (x_margin, y),
                    "실시간 상세 분석",
                    font=self._font_title,
                    fill=self.COLOR_WHITE,
                )
                y += 40

                if target_evt and target_evt["type"] == "RESPONSE":
                    info = target_evt["info"]

                    # 1. 유사도 (Progress Bar)
                    sim_score = info.similarity if info.similarity is not None else 0.0
                    sim_percent = int(sim_score * 100)
                    sim_pass = sim_score >= th_sim

                    draw.text(
                        (x_margin, y),
                        "말하기 정확도 (유사도)",
                        font=self._font_text,
                        fill=self.COLOR_GRAY_TEXT,
                    )
                    y += 30

                    # Bar Back
                    bar_w = 300
                    bar_h = 20
                    draw.rectangle(
                        [(x_margin, y), (x_margin + bar_w, y + bar_h)],
                        fill=(60, 60, 60),
                    )
                    # Bar Fill
                    fill_w = int(bar_w * min(1.0, sim_score))
                    bar_color = self.COLOR_SUCCESS if sim_pass else self.COLOR_GRAY_TEXT
                    draw.rectangle(
                        [(x_margin, y), (x_margin + fill_w, y + bar_h)],
                        fill=bar_color,
                    )

                    # Text score
                    draw.text(
                        (x_margin + bar_w + 15, y - 2),
                        f"{sim_percent}%",
                        font=self._font_text,
                        fill=self.COLOR_WHITE,
                    )

                    # Threshold Indicator (작은 선)
                    th_x = x_margin + int(bar_w * th_sim)
                    draw.line(
                        [(th_x, y - 5), (th_x, y + bar_h + 5)],
                        fill=self.COLOR_WARN,
                        width=2,
                    )
                    y += 40

                    # 2. 목소리 톤 (Pitch)
                    draw.text(
                        (x_margin, y),
                        "목소리 톤",
                        font=self._font_text,
                        fill=self.COLOR_GRAY_TEXT,
                    )
                    f0 = info.child_mean_f0
                    pitch_msg = "분석 불가"
                    pitch_col = self.COLOR_GRAY_TEXT

                    if f0 is not None:
                        if f0 > th_pitch:
                            pitch_msg = "너무 높아요 (끼익 소리?)"
                            pitch_col = self.COLOR_WARN
                        else:
                            pitch_msg = "적당해요 (좋음)"
                            pitch_col = self.COLOR_SUCCESS

                    draw.text(
                        (x_margin + 150, y),
                        pitch_msg,
                        font=self._font_text,
                        fill=pitch_col,
                    )
                    y += 40

                    # 3. 억양 (Intonation)
                    draw.text(
                        (x_margin, y),
                        "억양 (리듬감)",
                        font=self._font_text,
                        fill=self.COLOR_GRAY_TEXT,
                    )
                    mad = info.child_mad_semitone
                    mad_msg = "분석 불가"
                    mad_col = self.COLOR_GRAY_TEXT

                    if mad is not None:
                        if mad < th_mad_min:
                            mad_msg = "너무 단조로워요"
                            mad_col = self.COLOR_WARN
                        elif mad > th_mad_max:
                            mad_msg = "노래 같아요 (너무 튐)"
                            mad_col = self.COLOR_WARN
                        else:
                            mad_msg = "자연스러워요 (좋음)"
                            mad_col = self.COLOR_SUCCESS

                    draw.text(
                        (x_margin + 150, y), mad_msg, font=self._font_text, fill=mad_col
                    )
                    y += 50

                    # 4. 최종 결과 Box
                    is_success = info.success
                    res_bg = self.COLOR_SUCCESS if is_success else self.COLOR_FAIL
                    res_txt = "성 공!" if is_success else "실 패"
                    if not is_success and info.failure_reason:
                        # 이유 매핑
                        reason_map = {
                            "BAD_PROSODY": "목소리 톤/억양 불안정",
                            "LOW_SIMILARITY": "발음이 정확하지 않음",
                            "NO_RESPONSE": "반응 없음",
                            "NO_STIMULUS": "자극 없음",
                        }
                        fail_reason = reason_map.get(
                            info.failure_reason, info.failure_reason
                        )
                        res_txt += f": {fail_reason}"

                    draw.rectangle(
                        [(x_margin, y), (self.SIDEBAR_WIDTH - x_margin, y + 50)],
                        fill=res_bg,
                    )
                    # Center Text
                    bbox = draw.textbbox((0, 0), res_txt, font=self._font_title)
                    w_t = bbox[2] - bbox[0]
                    h_t = bbox[3] - bbox[1]
                    draw.text(
                        (
                            x_margin + (self.SIDEBAR_WIDTH - 2 * x_margin - w_t) // 2,
                            y + (50 - h_t * 1.5) // 2,
                        ),
                        res_txt,
                        font=self._font_title,
                        fill=(255, 255, 255),
                    )

                else:
                    draw.text(
                        (x_margin, y),
                        "분석 결과를 기다리는 중...",
                        font=self._font_text,
                        fill=(100, 100, 100),
                    )

                y += 100

                # --- [ SECTION 4: Summary ] ---
                draw.line(
                    [(x_margin, y), (self.SIDEBAR_WIDTH - x_margin, y)],
                    fill=(100, 100, 100),
                    width=2,
                )
                y += 30
                draw.text(
                    (x_margin, y),
                    "따라말하기 성공",
                    font=self._font_title,
                    fill=self.COLOR_WHITE,
                )

                stars = "★ " * curr_success_count + "☆ " * (
                    total_reps - curr_success_count
                )
                draw.text(
                    (x_margin + 200, y),
                    stars,
                    font=self._font_title,
                    fill=self.COLOR_WARN,
                )

                # Canvas -> OpenCV
                canvas_np = np.array(canvas)
                final_frame = cv2.cvtColor(canvas_np, cv2.COLOR_RGB2BGR)

                out.write(final_frame)
                current_frame += 1

        except Exception as e:
            logger.exception(f"시각화 중 오류 발생: {e}")
        finally:
            if cap:
                cap.release()
            if out:
                out.release()
            logger.info(f"시각화 종료: {output_path}")
