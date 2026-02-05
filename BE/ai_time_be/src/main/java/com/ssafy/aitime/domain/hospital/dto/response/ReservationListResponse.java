package com.ssafy.aitime.domain.hospital.dto.response;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;

import java.time.LocalDate;
import java.time.Period;
import java.util.UUID;

public record ReservationListResponse(
        UUID hospitalChildrenId,
        UUID childId,
        String name,
        Integer months,
        Gender gender,
        ExamStatus examStatus,
        Boolean isSubmitted
) {
    /**
     * Child와 Exam 정보로부터 DTO 생성
     *
     * @param hospitalChildrenId 병원 환아 ID
     * @param child 아이 엔티티
     * @param exam 검사 엔티티 (null 가능)
     * @return ReservationListResponse
     */
    public static ReservationListResponse of(UUID hospitalChildrenId, Child child, Exam exam) {
        return new ReservationListResponse(
                hospitalChildrenId,
                child.getChildId(),
                child.getName(),
                calculateMonths(child.getBirthdate()),
                child.getGender(),
                exam != null ? exam.getExamStatus() : null,
                exam != null ? exam.isSubmitted() : null
        );
    }

    /**
     * 생년월일로부터 개월 수 계산
     */
    private static Integer calculateMonths(LocalDate birthdate) {
        if (birthdate == null) {
            return null;
        }
        return (int) Period.between(birthdate, LocalDate.now()).toTotalMonths();
    }
}
