package com.ssafy.aitime.domain.child.dto.response;

import com.ssafy.aitime.domain.child.entity.enums.Gender;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public record ChildHomeResponse(
        UUID childId,
        String name,
        Gender gender,
        boolean isExamEligible,
        int examProgress,
        boolean hasPreviousExam,
        LocalDate nextEligibleAt,
        List<HospitalInfo> linkedHospitals
) {
}
