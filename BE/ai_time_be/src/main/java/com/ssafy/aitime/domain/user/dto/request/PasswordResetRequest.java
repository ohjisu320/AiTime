package com.ssafy.aitime.domain.user.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.util.UUID;

public record PasswordResetRequest(
        @NotNull UUID userId,
        @NotBlank String password
) {
}
