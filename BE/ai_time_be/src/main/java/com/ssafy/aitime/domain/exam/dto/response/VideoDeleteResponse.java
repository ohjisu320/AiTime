package com.ssafy.aitime.domain.exam.dto.response;

import lombok.Builder;

@Builder
public record VideoDeleteResponse(
        String examId,
        String videoType,
        String videoId,
        boolean deletedFromStorage,
        String status
) {}