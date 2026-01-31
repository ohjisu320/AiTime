package com.ssafy.aitime.domain.screening.dto.request;

import jakarta.validation.constraints.NotNull;

import java.util.UUID;

public record StartScreeningRequest(
        @NotNull(message = "아이 ID는 필수입니다.")
        UUID childId  // 어떤 아이의 스크리닝인지
) {
}
