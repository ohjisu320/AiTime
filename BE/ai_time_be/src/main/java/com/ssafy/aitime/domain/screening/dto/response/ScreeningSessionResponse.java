package com.ssafy.aitime.domain.screening.dto.response;

import com.ssafy.aitime.domain.screening.entity.enums.ScreeningStatus;

import java.time.LocalDateTime;
import java.util.UUID;

public record ScreeningSessionResponse(
        UUID sessionId,
        String roomName,
        String userToken,      // 프론트가 LiveKit 접속할 토큰
        ScreeningStatus status,
        LocalDateTime createdAt
) {
}
