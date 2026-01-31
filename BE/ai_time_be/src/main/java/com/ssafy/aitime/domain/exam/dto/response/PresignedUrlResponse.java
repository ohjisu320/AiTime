package com.ssafy.aitime.domain.exam.dto.response;

import lombok.Builder;

import java.time.LocalDateTime;
import java.util.Map;

@Builder
public record PresignedUrlResponse(
        String videoId,
        String examId,
        String videoType,
        String bucket,
        String s3Key,
        String uploadUrl,
        Map<String, String> requiredHeaders,
        LocalDateTime expiresAt
) {
}