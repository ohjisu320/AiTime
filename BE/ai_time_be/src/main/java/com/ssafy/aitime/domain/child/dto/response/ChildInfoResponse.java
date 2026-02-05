package com.ssafy.aitime.domain.child.dto.response;

import com.ssafy.aitime.domain.child.entity.enums.Gender;

import java.util.UUID;

public record ChildInfoResponse(
        UUID childId,
        String name,
        long months,
        Gender gender
) {
}
