package com.ssafy.aitime.domain.auth.dto.request;

import jakarta.validation.constraints.NotBlank;

public record PhoneVerifyRequest(
        @NotBlank String phoneNumber,
        @NotBlank String verificationCode
) {
}
