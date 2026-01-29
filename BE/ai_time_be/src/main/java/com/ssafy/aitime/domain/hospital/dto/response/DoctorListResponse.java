package com.ssafy.aitime.domain.hospital.dto.response;

import java.util.UUID;

public record DoctorListResponse(
        UUID doctorId,
        String doctorName
) {
}
