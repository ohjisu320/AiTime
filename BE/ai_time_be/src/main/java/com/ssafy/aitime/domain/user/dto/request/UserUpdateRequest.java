package com.ssafy.aitime.domain.user.dto.request;

import jakarta.validation.constraints.NotBlank;

public record UserUpdateRequest(
        @NotBlank String name,
        @NotBlank String phoneNumber
) {
}
