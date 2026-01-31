package com.ssafy.aitime.domain.hospital.dto.request;

import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
public record ReservationCreateRequest(
        UUID hospitalChildrenId,
        LocalDateTime scheduledAt,
        UUID doctorId
) {
}
