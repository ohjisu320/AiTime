package com.ssafy.aitime.domain.auth.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record PhoneVerificationRequest(
        @NotBlank(message = "휴대폰 번호는 필수 입력 값입니다.")
        @Pattern(regexp = "^010\\d{7,8}$", message = "올바른 휴대폰 번호 형식이 아닙니다.")
        String phoneNumber
) {
}
