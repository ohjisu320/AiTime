package com.ssafy.aitime.domain.exam.dto.response;

import com.ssafy.aitime.domain.child.entity.enums.ChildHomeStatus;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * ExamService에서 ChildService로 검사 정보를 전달하기 위한 DTO
 * 도메인 간 결합도를 낮추기 위해 서비스 레이어에서 DTO로 변환하여 전달
 */
public record ExamSummaryDTO(
        ChildHomeStatus childHomeStatus,        // 계산된 검사 상태
        Integer examProgress,              // 업로드된 비디오 개수 (0~4)
        LocalDate examStartedAt,           // 검사 시작일
        LocalDate nextEligibleAt,          // 다음 검사 가능일
        LocalDateTime draftExpiresAt       // 임시 검사 만료일시
) {
    /**
     * 검사 기록이 없는 경우의 기본값
     */
    public static ExamSummaryDTO empty() {
        return new ExamSummaryDTO(
                ChildHomeStatus.NEED_HOSPITAL,
                0,
                null,
                null,
                null
        );
    }
}
