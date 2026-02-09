package com.ssafy.aitime.domain.exam.dto.response;

import lombok.Builder;

import java.time.LocalDateTime;

@Builder
public record PresignedViewUrlResponse(
        String examId,
        String videoId,
        String bucket,
        String s3Key,
        String viewUrl,
        LocalDateTime expiresAt
) {}