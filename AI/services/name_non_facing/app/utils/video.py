# services/name_non_facing/app/utils/video.py
"""
비디오 프레임 추출 유틸리티

비디오 파일에서 프레임을 추출하고 관련 메타데이터를 제공합니다.

설계 의도:
    1. FPS 샘플링으로 효율적인 분석
       - 30fps 비디오를 10fps로 다운샘플링하여 연산량 감소
       
    2. 시간 동기화
       - 프레임 인덱스와 실제 시간(초) 매핑
       - 오디오 타임스탬프와 동기화 가능

Reference:
    - OpenCV VideoCapture: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Generator
import logging

import cv2
import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """비디오 메타데이터"""
    width: int
    height: int
    fps: float
    frame_count: int
    duration_sec: float
    
    @property
    def frame_size(self) -> Tuple[int, int]:
        """(width, height) 튜플 반환"""
        return (self.width, self.height)


@dataclass
class FrameData:
    """프레임 데이터와 타임스탬프"""
    frame: np.ndarray       # BGR 이미지
    timestamp: float        # 초 단위 시간
    frame_index: int        # 원본 프레임 인덱스


def get_video_info(video_path: str) -> VideoInfo:
    """
    비디오 메타데이터 추출
    
    Args:
        video_path: 비디오 파일 경로
        
    Returns:
        VideoInfo: 비디오 정보
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        ValueError: 비디오를 열 수 없을 때
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"비디오 파일이 존재하지 않습니다: {video_path}")
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
    
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = frame_count / fps if fps > 0 else 0.0
        
        return VideoInfo(
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            duration_sec=duration_sec
        )
    finally:
        cap.release()


def extract_frames(
    video_path: str,
    target_fps: Optional[int] = None,
    start_time: float = 0.0,
    end_time: Optional[float] = None
) -> Tuple[List[np.ndarray], List[float], VideoInfo]:
    """
    비디오에서 프레임 추출 (FPS 샘플링 지원)
    
    Args:
        video_path: 비디오 파일 경로
        target_fps: 목표 FPS (None이면 config에서 가져옴)
        start_time: 시작 시간 (초)
        end_time: 종료 시간 (초, None이면 끝까지)
        
    Returns:
        Tuple[List[np.ndarray], List[float], VideoInfo]:
            - frames: 프레임 이미지 목록
            - timestamps: 각 프레임의 타임스탬프 (초)
            - video_info: 비디오 메타데이터
            
    Note:
        - 메모리 사용량 주의: 긴 비디오는 generator 버전 사용 권장
    """
    settings = get_settings()
    target_fps = target_fps or settings.VIDEO_FPS_SAMPLE
    
    video_info = get_video_info(video_path)
    original_fps = video_info.fps
    
    # 샘플링 간격 계산 (target_fps가 0이면 원본 FPS 유지)
    if target_fps <= 0 or target_fps >= original_fps:
        sample_interval = 1
        effective_fps = original_fps
    else:
        sample_interval = int(round(original_fps / target_fps))
        effective_fps = target_fps
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
    
    frames = []
    timestamps = []
    
    try:
        # 시작 위치로 이동
        if start_time > 0:
            start_frame = int(start_time * original_fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        end_frame = None
        if end_time is not None:
            end_frame = int(end_time * original_fps)
        
        frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        sampled_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            
            # 종료 조건
            if end_frame is not None and current_frame >= end_frame:
                break
            
            # 샘플링 조건
            if (current_frame - frame_idx) % sample_interval == 0:
                timestamp = current_frame / original_fps
                frames.append(frame)
                timestamps.append(timestamp)
                sampled_count += 1
        
        if sample_interval == 1:
            logger.info(
                f"🎬 프레임 추출 완료: {sampled_count}개 "
                f"(원본 {video_info.frame_count}프레임, {original_fps:.1f}fps 유지)"
            )
        else:
            logger.info(
                f"🎬 프레임 추출 완료: {sampled_count}개 "
                f"(원본 {video_info.frame_count}프레임, "
                f"{original_fps:.1f}fps → {effective_fps}fps 샘플링)"
            )
        
        return frames, timestamps, video_info
        
    finally:
        cap.release()


def extract_frames_generator(
    video_path: str,
    target_fps: Optional[int] = None,
    start_time: float = 0.0,
    end_time: Optional[float] = None
) -> Generator[FrameData, None, None]:
    """
    비디오에서 프레임 추출 (Generator 버전 - 메모리 효율적)
    
    Args:
        video_path: 비디오 파일 경로
        target_fps: 목표 FPS
        start_time: 시작 시간 (초)
        end_time: 종료 시간 (초)
        
    Yields:
        FrameData: 프레임 데이터
    """
    settings = get_settings()
    target_fps = target_fps or settings.VIDEO_FPS_SAMPLE
    
    video_info = get_video_info(video_path)
    original_fps = video_info.fps
    
    # 샘플링 간격
    if target_fps >= original_fps:
        sample_interval = 1
    else:
        sample_interval = int(round(original_fps / target_fps))
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
    
    try:
        if start_time > 0:
            start_frame = int(start_time * original_fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        end_frame = None
        if end_time is not None:
            end_frame = int(end_time * original_fps)
        
        frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            
            if end_frame is not None and current_frame >= end_frame:
                break
            
            if (current_frame - frame_idx) % sample_interval == 0:
                timestamp = current_frame / original_fps
                yield FrameData(
                    frame=frame,
                    timestamp=timestamp,
                    frame_index=current_frame
                )
    finally:
        cap.release()


def get_frame_at_time(video_path: str, time_sec: float) -> Optional[np.ndarray]:
    """
    특정 시간의 프레임 추출
    
    Args:
        video_path: 비디오 파일 경로
        time_sec: 추출할 시간 (초)
        
    Returns:
        프레임 이미지 또는 None (범위 초과 시)
    """
    video_info = get_video_info(video_path)
    
    if time_sec < 0 or time_sec > video_info.duration_sec:
        return None
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    
    try:
        target_frame = int(time_sec * video_info.fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
        ret, frame = cap.read()
        return frame if ret else None
    finally:
        cap.release()


def frames_to_video(
    frames: List[np.ndarray],
    output_path: str,
    fps: float = 10.0,
    codec: str = "mp4v"
) -> None:
    """
    프레임 목록을 비디오 파일로 저장 (디버깅/시각화용)
    
    Args:
        frames: 프레임 이미지 목록
        output_path: 출력 파일 경로
        fps: 출력 FPS
        codec: 비디오 코덱
    """
    if not frames:
        raise ValueError("프레임 목록이 비어있습니다")
    
    height, width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*codec)
    
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    try:
        for frame in frames:
            writer.write(frame)
        logger.info(f"🎬 비디오 저장 완료: {output_path}")
    finally:
        writer.release()
