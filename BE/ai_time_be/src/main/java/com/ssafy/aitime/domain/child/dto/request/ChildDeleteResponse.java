package com.ssafy.aitime.domain.child.dto.request;

import com.ssafy.aitime.common.enums.RecordStatus;

import java.util.UUID;

public record ChildDeleteResponse(
        UUID childId,
        RecordStatus status
) {
}
