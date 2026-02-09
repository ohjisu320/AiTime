package com.ssafy.aitime.domain.exam.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;

@Schema(description = "검사 시작 요청")
public record ExamStartRequest(
        @Schema(description = "비디오 촬영 동의 여부", example = "true")
        @NotNull(message = "비디오 동의 여부는 필수입니다")
        Boolean videoConsent
) {
}