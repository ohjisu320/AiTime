package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryDTO;

import java.util.Optional;
import java.util.UUID;

public interface ExamService {
    /**
     * 특정 아이의 홈 화면용 검사 요약 정보 조회
     * 검사 상태를 ChildHomeStatus enum으로 계산하여 반환
     *
     * @param childId 아이 ID
     * @return 검사 요약 정보 DTO
     */
    ExamSummaryDTO getExamSummaryForChild(UUID childId);
}
