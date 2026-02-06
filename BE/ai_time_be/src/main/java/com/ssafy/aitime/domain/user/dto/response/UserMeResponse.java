package com.ssafy.aitime.domain.user.dto.response;

import java.util.UUID;

public record UserMeResponse(
        UUID userId,
        String name,
        String phoneNumber,
        String loginId
) {
}
