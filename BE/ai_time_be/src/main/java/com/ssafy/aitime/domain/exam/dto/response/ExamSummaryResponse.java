package com.ssafy.aitime.domain.exam.dto.response;

import java.time.LocalDateTime;

public record ExamSummaryResponse(
        boolean isExamEligible,
        int examProgress,
        boolean hasPreviousExam,
        LocalDateTime nextEligibleAt
) {}
