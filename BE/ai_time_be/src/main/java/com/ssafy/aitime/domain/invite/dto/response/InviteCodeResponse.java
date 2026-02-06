package com.ssafy.aitime.domain.invite.dto.response;

import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;


public record InviteCodeResponse(
        UUID inviteCodeId,
        String inviteCode,
        String childName,
        String parentPhone,
        InviteCodeStatus status,
        LocalDateTime createdAt
) {
}
