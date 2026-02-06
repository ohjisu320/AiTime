package com.ssafy.aitime.domain.user.dto.request;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotBlank;

public record UserJoinRequest(
        @NotBlank String loginId,
        @NotBlank String password,
        @NotBlank String name,
        @NotBlank String phoneNumber,
        @AssertTrue(message = "필수 약관에 동의해야 합니다.")
        boolean privacyAgreed
) {
}
