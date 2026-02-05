package com.ssafy.aitime.domain.user.dto.response;

import java.util.UUID;

public record UserIdentityResponse(
        boolean isVerified,
        UUID userId
) {
}
