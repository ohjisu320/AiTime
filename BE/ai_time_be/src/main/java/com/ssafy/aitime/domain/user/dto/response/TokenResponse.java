package com.ssafy.aitime.domain.user.dto.response;

import com.ssafy.aitime.domain.user.service.dto.UserInfoDTO;

public record TokenResponse(
    String accessToken,
    String refreshToken,
    UserInfoDTO user
) {
}
