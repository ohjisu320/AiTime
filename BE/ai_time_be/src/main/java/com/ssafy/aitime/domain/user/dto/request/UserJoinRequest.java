package com.ssafy.aitime.domain.user.dto.request;

import jakarta.validation.constraints.NotBlank;

public record UserJoinRequest(
        @NotBlank String loginId,
        @NotBlank String password,
        @NotBlank String name,
        @NotBlank String phoneNumber,
        boolean privacyAgreed
) {
}
