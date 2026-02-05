package com.ssafy.aitime.domain.screening.dto.response;

import com.ssafy.aitime.domain.screening.entity.enums.ScreeningStatus;

import java.util.UUID;

public record ScreeningStatusResponse(
        UUID sessionId,
        String roomName,
        ScreeningStatus status,
        String message  // "스크리닝 진행 중", "녹화 준비 완료" 등
) {
}
