package com.ssafy.aitime.domain.child.dto.response;

import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalInfoDTO;

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
        List<HospitalInfoDTO> linkedHospitals
) {
}
