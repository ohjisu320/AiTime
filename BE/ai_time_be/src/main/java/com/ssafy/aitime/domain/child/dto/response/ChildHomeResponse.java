package com.ssafy.aitime.domain.child.dto.response;

import com.ssafy.aitime.domain.child.entity.enums.ChildHomeStatus;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalInfoDTO;

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
        ChildHomeStatus examStatus,        // 검사 상태 (통합 enum)
        Integer examProgress,              // 진행 중인 검사의 업로드된 비디오 개수 (0~4)
        LocalDate examStartedAt,           // 검사 시작일 (첫 비디오 촬영일)
        LocalDate nextEligibleAt,          // 다음 검사 가능일
        LocalDateTime draftExpiresAt,      // 임시 검사 만료일시 (3일)
        List<HospitalInfoDTO> linkedHospitals  // 연동된 병원 목록
) {
}
