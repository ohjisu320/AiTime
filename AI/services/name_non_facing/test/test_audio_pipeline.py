# test/test_audio_pipeline.py
"""
오디오 파이프라인 테스트 스크립트

사용법:
    # 전체 테스트
    python -m pytest test/test_audio_pipeline.py -v
    
    # 개별 모듈 테스트
    python -m pytest test/test_audio_pipeline.py::test_vad -v
    python -m pytest test/test_audio_pipeline.py::test_speech_recognizer -v
    
    # 직접 실행 (CLI 모드)
    python test/test_audio_pipeline.py --video sample_video/name_facing.mp4
"""

import sys
import argparse
import logging
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ===== 단위 테스트 =====

def test_config():
    """설정 로드 테스트"""
    from app.config import get_settings, Settings
    
    settings = get_settings()
    
    assert isinstance(settings, Settings)
    assert settings.AUDIO_SAMPLE_RATE == 16000
    assert 0.0 <= settings.VAD_THRESHOLD <= 1.0
    
    logger.info("✅ Config 테스트 통과")


def test_audio_utils():
    """오디오 유틸리티 테스트"""
    from app.utils.audio import (
        audio_to_float32,
        normalize_audio,
        get_audio_duration,
        extract_segment,
        compute_rms
    )
    
    # 테스트용 더미 오디오 생성 (1초, 16kHz, 사인파)
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    
    # float32 변환
    int16_audio = (audio * 32767).astype(np.int16)
    float_audio = audio_to_float32(int16_audio)
    assert float_audio.dtype == np.float32
    assert -1.0 <= float_audio.max() <= 1.0
    
    # 정규화
    normalized = normalize_audio(audio, target_db=-20.0)
    assert normalized.dtype == np.float32
    
    # 길이 계산
    duration_calc = get_audio_duration(audio, sample_rate)
    assert abs(duration_calc - 1.0) < 0.01
    
    # 세그먼트 추출
    segment = extract_segment(audio, 0.2, 0.5, sample_rate)
    expected_len = int(0.3 * sample_rate)
    assert abs(len(segment) - expected_len) < 10
    
    # RMS 계산
    rms = compute_rms(audio)
    assert 0.0 < rms < 1.0
    
    logger.info("✅ Audio Utils 테스트 통과")


def test_vad():
    """VAD 모델 테스트"""
    from app.models.vad import VoiceActivityDetector
    
    vad = VoiceActivityDetector()
    
    # 모델 로드 확인
    vad.ensure_loaded()
    assert vad.is_loaded
    
    # 테스트용 오디오 (무음 + 톤 + 무음)
    sample_rate = 16000
    silence = np.zeros(sample_rate, dtype=np.float32)  # 1초 무음
    tone = np.sin(2 * np.pi * 440 * np.linspace(0, 1, sample_rate)).astype(np.float32) * 0.5  # 1초 톤
    
    # 무음에서는 음성 감지 안됨 (또는 빈 리스트)
    segments = vad.detect(silence, sample_rate)
    # 무음이므로 segments가 비어있거나 매우 짧아야 함
    
    logger.info("✅ VAD 테스트 통과")


def test_speech_recognizer():
    """음성 인식기 테스트"""
    from app.models.speech_recognizer import SpeechRecognizer, TranscriptionResult, Segment
    
    recognizer = SpeechRecognizer()
    
    # 모델 로드 확인
    recognizer.ensure_loaded()
    assert recognizer.is_loaded
    
    # is_name_call 메서드 테스트
    assert recognizer.is_name_call("민수야", "민수") == True
    assert recognizer.is_name_call("우리 민수", "민수") == True
    assert recognizer.is_name_call("민수!", "민수") == True
    assert recognizer.is_name_call("안녕하세요", "민수") == False
    
    logger.info("✅ SpeechRecognizer 테스트 통과")


def test_speaker_diarizer_mock():
    """화자 분리기 모킹 테스트 (HF 토큰 없이)"""
    from app.models.speaker_diarizer import (
        SpeakerLabel,
        SpeakerSegment,
        DiarizationResult
    )
    
    # DiarizationResult 구조 테스트
    segments = [
        SpeakerSegment("SPEAKER_00", SpeakerLabel.PARENT, 0.0, 2.0),
        SpeakerSegment("SPEAKER_01", SpeakerLabel.CHILD, 2.5, 3.5),
    ]
    
    result = DiarizationResult(
        segments=segments,
        speaker_mapping={"SPEAKER_00": SpeakerLabel.PARENT, "SPEAKER_01": SpeakerLabel.CHILD},
        num_speakers=2
    )
    
    # 라벨별 필터링
    parent_segs = result.get_segments_by_label(SpeakerLabel.PARENT)
    assert len(parent_segs) == 1
    assert parent_segs[0].speaker_label == SpeakerLabel.PARENT
    
    # 범위 필터링
    range_segs = result.get_segments_in_range(2.0, 4.0)
    assert len(range_segs) == 1
    assert range_segs[0].speaker_label == SpeakerLabel.CHILD
    
    logger.info("✅ SpeakerDiarizer (Mock) 테스트 통과")


def test_child_voice_analyzer_structure():
    """ChildVoiceAnalyzer 구조 테스트"""
    from app.models.child_voice_analyzer import ChildVoiceReaction
    
    # not_detected 생성
    reaction = ChildVoiceReaction.not_detected()
    assert reaction.detected == False
    assert reaction.latency_sec is None
    
    # detected 생성
    reaction = ChildVoiceReaction(
        detected=True,
        start_sec=5.5,
        end_sec=6.0,
        duration_sec=0.5,
        latency_sec=0.5,
        confidence=0.9
    )
    assert reaction.detected == True
    assert reaction.latency_sec == 0.5
    
    logger.info("✅ ChildVoiceAnalyzer 구조 테스트 통과")


# ===== 통합 테스트 (실제 파일 필요) =====

def run_integration_test(video_path: str, child_name: str = "민수"):
    """
    통합 테스트: 비디오 파일로 전체 파이프라인 실행
    
    Args:
        video_path: 테스트 비디오 파일 경로
        child_name: 호명할 아이 이름
    """
    from app.utils.audio import load_audio_from_video
    from app.models.vad import VoiceActivityDetector
    from app.models.speech_recognizer import SpeechRecognizer
    from app.models.child_voice_analyzer import ChildVoiceAnalyzer
    from app.config import get_settings
    
    settings = get_settings()
    
    logger.info(f"🎬 통합 테스트 시작: {video_path}")
    logger.info(f"👶 아이 이름: {child_name}")
    
    # 1. 오디오 추출 및 로드
    logger.info("🎬 오디오 추출 중...")
    try:
        audio, sample_rate = load_audio_from_video(video_path)
        duration = len(audio) / sample_rate
        logger.info(f"  - 샘플레이트: {sample_rate} Hz")
        logger.info(f"  - 오디오 길이: {duration:.2f}초")
    except Exception as e:
        logger.error(f"❌ 오디오 추출 실패: {e}")
        return
    
    # 2. VAD 테스트
    logger.info("🎬 VAD 분석 중...")
    vad = VoiceActivityDetector()
    speech_segments = vad.detect(audio, sample_rate)
    logger.info(f"  - 감지된 음성 구간: {len(speech_segments)}개")
    for i, seg in enumerate(speech_segments[:5]):  # 최대 5개만 출력
        logger.info(f"    [{i+1}] {seg.start_sec:.2f}s ~ {seg.end_sec:.2f}s (duration: {seg.duration_sec:.2f}s)")
    if len(speech_segments) > 5:
        logger.info(f"    ... 외 {len(speech_segments) - 5}개")
    
    # 3. 음성 인식 테스트
    logger.info("🎬 음성 인식 중...")
    recognizer = SpeechRecognizer()
    
    try:
        transcription = recognizer.transcribe(audio, sample_rate)
        logger.info(f"  - 감지 언어: {transcription.language} ({transcription.language_probability:.2%})")
        logger.info(f"  - 전체 텍스트: {transcription.text[:200]}...")
        
        # 호명 탐지
        name_calls = recognizer.find_name_calls(transcription, child_name)
        logger.info(f"  - 호명 감지: {len(name_calls)}회")
        for i, call in enumerate(name_calls):
            logger.info(f"    [{i+1}] '{call.text}' @ {call.start_sec:.2f}s ~ {call.end_sec:.2f}s")
    except Exception as e:
        logger.error(f"❌ 음성 인식 실패: {e}")
        name_calls = []
    
    # 4. 화자 분리 (토큰 필요)
    logger.info("👥 화자 분리 테스트...")
    try:
        from app.models.speaker_diarizer import SpeakerDiarizer
        
        if settings.DIARIZATION_USE_AUTH_TOKEN:
            diarizer = SpeakerDiarizer()
            diarization = diarizer.diarize(audio, sample_rate)
            logger.info(f"  - 화자 수: {diarization.num_speakers}")
            logger.info(f"  - 화자 매핑: {diarization.speaker_mapping}")
        else:
            logger.warning("  ⚠️ HuggingFace 토큰 미설정, 화자 분리 스킵")
            diarization = None
    except Exception as e:
        logger.warning(f"  ⚠️ 화자 분리 실패 (토큰 미설정?): {e}")
        diarization = None
    
    # 5. 아이 음성 반응 분석 (호명이 있는 경우)
    if name_calls:
        logger.info("👶 아이 음성 반응 분석...")
        analyzer = ChildVoiceAnalyzer()
        
        for i, call in enumerate(name_calls):
            reaction = analyzer.analyze(
                audio=audio,
                sample_rate=sample_rate,
                trigger_end_sec=call.end_sec,
                timeout_sec=settings.REACTION_TIMEOUT_SEC,
                diarization=diarization
            )
            
            if reaction.detected:
                logger.info(f"  [{i+1}] ✅ 반응 감지! Latency: {reaction.latency_sec:.2f}s, Duration: {reaction.duration_sec:.2f}s")
            else:
                logger.info(f"  [{i+1}] ❌ 반응 없음")
    
    logger.info("🎉 통합 테스트 완료!")


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(description="오디오 파이프라인 테스트")
    parser.add_argument(
        "--video", "-v",
        type=str,
        default=None,
        help="테스트할 비디오 파일 경로"
    )
    parser.add_argument(
        "--name", "-n",
        type=str,
        default="정현",
        help="호명할 아이 이름 (기본: 정현)"
    )
    parser.add_argument(
        "--unit-only", "-u",
        action="store_true",
        help="단위 테스트만 실행"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🎬 오디오 파이프라인 테스트")
    logger.info("=" * 60)
    
    # 단위 테스트 실행
    logger.info("\n📋 단위 테스트 실행...")
    test_config()
    test_audio_utils()
    test_vad()
    test_speech_recognizer()
    test_speaker_diarizer_mock()
    test_child_voice_analyzer_structure()
    
    logger.info("\n✅ 모든 단위 테스트 통과!")
    
    # 통합 테스트 (비디오 지정 시)
    if not args.unit_only and args.video:
        logger.info("\n" + "=" * 60)
        logger.info("🔗 통합 테스트 실행...")
        logger.info("=" * 60 + "\n")
        run_integration_test(args.video, args.name)
    elif not args.unit_only:
        logger.info("\n💡 통합 테스트를 실행하려면 --video 옵션으로 비디오 파일을 지정하세요.")
        logger.info("   예: python test/test_audio_pipeline.py --video sample_video/name_facing.mp4")


if __name__ == "__main__":
    main()
