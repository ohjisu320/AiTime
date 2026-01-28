package com.ssafy.aitime.domain.child.dto.response;

import com.ssafy.aitime.domain.child.entity.enums.ChildHomeStatus;
import com.ssafy.aitime.domain.child.entity.enums.Gender;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 아이 홈 화면 조회 응답 DTO
 * 기존의 여러 boolean 값들을 ChildHomeStatus enum으로 통합하여
 * 프론트엔드에서 간단한 switch 문으로 분기 처리 가능
 */
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
