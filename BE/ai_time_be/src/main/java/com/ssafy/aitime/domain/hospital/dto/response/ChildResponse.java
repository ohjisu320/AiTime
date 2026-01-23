package com.ssafy.aitime.domain.hospital.dto.response;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

public record ChildResponse(
        UUID childId,
        UUID userId,
        String name,
        int monthlyAge,
        LocalDate birthdate,
        String gender,
        String latestExamStatus
) {
}
