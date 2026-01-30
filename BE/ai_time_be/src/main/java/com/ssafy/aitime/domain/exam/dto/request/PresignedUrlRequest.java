package com.ssafy.aitime.domain.exam.dto.request;

import jakarta.validation.constraints.NotBlank;

public record PresignedUrlRequest(
        @NotBlank(message = "examId는 필수입니다")
        String examId,

        @NotBlank(message = "videoType은 필수입니다")
        String videoType
) {
}