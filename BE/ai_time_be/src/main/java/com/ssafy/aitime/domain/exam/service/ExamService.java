package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.exam.dto.response.ExamInfoResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamStartResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryDTO;
import com.ssafy.aitime.domain.exam.entity.Exam;

import java.util.List;
import java.util.Map;
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

    /**
     * 검사 생성 - Child 엔티티를 받아서 검사 생성
     * ChildService에서 권한 확인 후 호출됨
     *
     * @param child Child 엔티티
     * @return 생성된 검사 정보
     */
    ExamStartResponse createExam(Child child);
    Map<UUID, Exam> getLatestExamsByChildIds(List<UUID> childIds);

    /**
     * 검사 진행도 조회 - 4개의 태스크별 영상 업로드 완료 여부 확인
     * Child 도메인에서 권한 확인 및 개월 수 검증 후 호출됨
     */
    ExamInfoResponse getExamInfo(UUID childId, boolean underEighteen);
}
