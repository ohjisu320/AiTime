package com.ssafy.aitime.domain.hospital.dto.response;

import java.util.List;

public record TotalPatientListResponse(
        List<ChildResponse> childResponses,
        long total) {
}
