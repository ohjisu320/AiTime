package com.ssafy.aitime.domain.hospital.dto.response;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

public record ChildResponse(
        UUID hospitalChildrenId,
        String childName,
        String gender,
        int months,
        LocalDateTime scheduledAt,
        String examStatus,
        boolean isSubmitted
) {
}
