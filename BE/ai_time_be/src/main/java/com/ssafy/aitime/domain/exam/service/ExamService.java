package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryResponse;

import java.util.Optional;
import java.util.UUID;

public interface ExamService {
    // 특정 아이의 홈 화면용 검사 요약 정보 조회
    Optional<ExamSummaryResponse> getExamSummaryForChild(UUID childId);
}
