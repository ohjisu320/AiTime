package com.ssafy.aitime.domain.exam.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public record PresignedKeyRequest(
        @NotBlank(message = "videoType은 필수입니다")
        String videoType,

        @NotBlank
        String contentType,  // 선택: 기본값 "video/mp4"

        @Positive(message = "contentLength는 양수여야 합니다")
        Long contentLength  // 선택: 용량 검증용
) {
        // 기본값 설정을 위한 생성자
        public PresignedKeyRequest {
                if (contentType == null || contentType.isBlank()) {
                        contentType = "video/mp4";
                }
        }
}