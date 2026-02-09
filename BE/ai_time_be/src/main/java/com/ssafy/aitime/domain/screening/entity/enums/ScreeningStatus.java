package com.ssafy.aitime.domain.screening.entity.enums;

public enum ScreeningStatus {
    PENDING,        // 세션 생성됨, AI 연결 대기 중
    IN_PROGRESS,    // 스크리닝 진행 중 (가이드 중)
    READY,          // 스크리닝 완료, 녹화 준비 완료
    FAILED,         // 실패 또는 중단
    TIMEOUT         // 시간 초과
}
