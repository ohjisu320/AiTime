package com.ssafy.aitime.domain.screening.dto.request;

import jakarta.validation.constraints.NotBlank;

public record ScreeningCompleteRequest(
        @NotBlank(message = "방 이름은 필수입니다.")
        String roomName,

        String status  // "success", "failure"
) {
}
