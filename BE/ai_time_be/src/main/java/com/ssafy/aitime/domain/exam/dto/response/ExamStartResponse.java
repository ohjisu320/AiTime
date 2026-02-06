package com.ssafy.aitime.domain.exam.dto.response;

import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import io.swagger.v3.oas.annotations.media.Schema;

import java.util.UUID;

@Schema(description = "검사 시작 응답")
public record ExamStartResponse(
        @Schema(description = "생성된 검사 ID")
        UUID examId,

        @Schema(description = "아이 ID")
        UUID childId,

        @Schema(description = "검사 상태", example = "IN_PROGRESS")
        ExamStatus status
) {
    public static ExamStartResponse of(UUID examId, UUID childId, ExamStatus status) {
        return new ExamStartResponse(examId, childId, status);
    }
}