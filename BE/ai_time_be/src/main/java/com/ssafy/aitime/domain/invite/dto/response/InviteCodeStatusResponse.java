package com.ssafy.aitime.domain.invite.dto.response;

import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;

import java.util.UUID;

public record InviteCodeStatusResponse(
        UUID inviteCodeId,
        InviteCodeStatus status,
        String childName
) {
}
