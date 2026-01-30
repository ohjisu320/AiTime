package com.ssafy.aitime.domain.exam.dto.response;

import lombok.Builder;

@Builder
public record PresignedUrlResponse(
        String videoId,
        String presignedUrl,
        String s3Key,
        Long expiresIn  // 초 단위
) {
}