from collections.abc import Callable

from app.rtn.config import (
    AnalysisConfig,
    ContactConfig,
    EmotionConfig,
    FaceDetConfig,
    FaceMeshConfig,
    GazeSmoothConfig,
    ROIConfig,
    RoleAssignConfig,
    TrackConfig,
    VADConfig,
)
from app.rtn.pipeline.video_analyzer import VideoAnalyzer
from app.rtn.settings import RTNConfig
from app.rtn.types import FrameBGR


def build_analyzer(
    window_s: float = 5.0,
    vad_merge_gap: float = 0.3,
    vad_min_speech_ms: int = 250,
    vad_min_silence_ms: int = 250,
    min_contact_frames: int = 3,
    warmup_s: float = 1.0,
    conf: float = 0.6,
    debug: bool = False,
    fps_override: float | None = None,
    # Emotion
    emotion_enable: bool = True,
    emotion_skip_frames: int = 5,
    emotion_model: str = "enet_b0_8_best_vgaf",
    debug_publish: Callable[[FrameBGR], None] | None = None,
    conf_th: float | None = None,
) -> VideoAnalyzer:
    vad_cfg = VADConfig(
        sr=16000,
        min_speech_ms=vad_min_speech_ms,
        min_silence_ms=vad_min_silence_ms,
        merge_gap_s=vad_merge_gap,
    )
    # face mesh:
    # - 얼굴 검출 신뢰도 임계값(conf)은 downstream(트래킹/역할/ROI) 안정성에 관여
    # - model_selection은 MediaPipe FaceDetection 옵션(거리/정확도 트레이드오프)
    #   -> cfg.face_det.model_selection 값으로 제어
    face_cfg = FaceDetConfig(min_conf=conf)

    # SORT/트래킹:
    # - max_age: 잠깐 놓친 트랙을 얼마나 유지할지(가림/회전 대비) ↔ 오탐 유지 위험
    # - min_hits: 트랙 확정까지 필요한 히트 수(초기 오탐 억제) ↔ 초기 지연 증가
    # - iou_threshold: 매칭 엄격도(아이/부모 근접 시 중요)
    track_cfg = TrackConfig()

    # 역할 할당:
    # - 초반 warmup 동안 트랙 안정화/영역 기반 판정에 사용(초기 흔들림 완화)
    role_cfg = RoleAssignConfig(warmup_s=warmup_s)

    # ROI
    # - 랜드마크/추정 노이즈를 흡수하기 위해 dilation 적용.
    # - mesh 실패(측면/가림) 시 bbox fallback은 불확실성이 커서 더 크게 잡음.
    roi_cfg = ROIConfig()

    # gaze:
    # 휴리스틱이라서 프레임 단위 노이즈 smoothing
    gaze_cfg = GazeSmoothConfig()

    # eye-contact 판정 튜닝:
    # - min_contact_frames: "순간 스파이크"를 접촉으로 오인하지 않도록 최소 지속 프레임
    # - raycast_samples: 추정 안정성(정확도)과 계산 비용 트레이드오프
    contact_cfg = ContactConfig(min_contact_frames=min_contact_frames)

    # 분석 창 길이
    # (window_s)는 응답 지연/유지시간 집계 범위를 결정
    analysis_cfg = AnalysisConfig(
        window_s=window_s, debug=debug, fps_override=fps_override
    )

    emotion_cfg = EmotionConfig(
        enable=emotion_enable,
        skip_frames=emotion_skip_frames,
        model_name=emotion_model,
    )

    return VideoAnalyzer(
        vad_cfg=vad_cfg,
        face_cfg=face_cfg,
        face_mesh_cfg=FaceMeshConfig(),
        crop_cfg=CropConfig(),
        track_cfg=track_cfg,
        role_cfg=role_cfg,
        roi_cfg=roi_cfg,
        gaze_cfg=gaze_cfg,
        contact_cfg=contact_cfg,
        analysis_cfg=analysis_cfg,
        emotion_cfg=emotion_cfg,
        conf_th=conf,
        debug_publish=debug_publish,
    )


def build_analyzer_from_cfg(
    cfg: RTNConfig,
    *,
    debug_publish: Callable[[FrameBGR], None] | None = None,
    conf_th: float | None = None,
) -> VideoAnalyzer:
    th = float(conf_th) if conf_th is not None else float(cfg.face_det.min_conf)

    return VideoAnalyzer(
        vad_cfg=cfg.vad,
        face_cfg=cfg.face_det,
        face_mesh_cfg=cfg.face_mesh,
        crop_cfg=cfg.crop,
        track_cfg=cfg.track,
        role_cfg=cfg.role,
        roi_cfg=cfg.roi,
        gaze_cfg=cfg.gaze,
        contact_cfg=cfg.contact,
        analysis_cfg=cfg.analysis,
        conf_th=th,
        debug_publish=debug_publish,
    )
