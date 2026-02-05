package com.ssafy.aitime.domain.auth.dto.response;

import com.fasterxml.jackson.annotation.JsonFormat;

import java.time.LocalDateTime;

public record PhoneVerificationResponse(
        String phoneNumber,

        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss", timezone = "Asia/Seoul")
        LocalDateTime expiredAt
) {
    public static PhoneVerificationResponse of(String phoneNumber, LocalDateTime expiredAt) {
        return new PhoneVerificationResponse(phoneNumber, expiredAt);
    }
}
