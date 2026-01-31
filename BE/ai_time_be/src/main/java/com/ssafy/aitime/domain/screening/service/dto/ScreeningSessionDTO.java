package com.ssafy.aitime.domain.screening.service.dto;

import com.ssafy.aitime.domain.screening.entity.enums.ScreeningStatus;

import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.UUID;

public record ScreeningSessionDTO(
        UUID sessionId,
        String roomName,
        UUID userId,
        ScreeningStatus status,
        String userParticipantId,  // 프론트엔드 참가자 ID
        String aiParticipantId,    // AI 참가자 ID
        LocalDateTime startedAt,   // 스크리닝 시작 시간
        LocalDateTime completedAt, // 스크리닝 완료 시간 (녹화 준비됨)
        LocalDateTime createdAt    // 세션 생성 시간
) implements Serializable {
    // Redis 키 생성
    public static String getRedisKey(String roomName) {
        return "screening:session:" + roomName;
    }

    public static String getUserSessionKey(UUID userId) {
        return "screening:user:" + userId;
    }
}
