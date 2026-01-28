package com.ssafy.aitime.domain.invite.dto.response;

import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;

import java.time.LocalDateTime;
import java.util.UUID;

public record InviteCodeRevokeResponse(
        UUID inviteCodeId,
        InviteCodeStatus status,
        LocalDateTime updatedAt
) {
}
