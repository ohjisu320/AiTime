package com.ssafy.aitime.domain.user.service.dto;

import com.ssafy.aitime.domain.user.entity.enums.UserRole;

import java.util.UUID;

public record UserInfoDTO(
        UUID userId,
        String name,
        UserRole userRole
) {
}
