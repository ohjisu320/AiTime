package com.ssafy.aitime.domain.hospital.dto.response;

import java.util.List;

public record PatientSearchResponse(
        List<ChildResponse> childResponses,
        long total
) {
}

