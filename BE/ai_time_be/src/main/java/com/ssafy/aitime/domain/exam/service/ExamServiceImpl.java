package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryResponse;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ExamServiceImpl implements ExamService {

    private final ExamRepository examRepository;
    private final VideoRepository videoRepository; // 비디오 개수 카운트용

    @Override
    @Transactional(readOnly = true)
    public Optional<ExamSummaryResponse> getExamSummaryForChild(UUID childId) {
        // 1. 가장 최신 검사 기록 조회
        Optional<Exam> latestExamOpt = examRepository.findFirstByChild_ChildIdOrderByCreatedAtDesc(childId);

        // 2. 검사 기록이 없으면 준비한 디폴트 값 즉시 반환 (Early Return)
        if (latestExamOpt.isEmpty()) {
            return Optional.of(new ExamSummaryResponse(false, 0, false, LocalDateTime.now()));
        }
        Exam latestExam = latestExamOpt.get();

        // 1) 다음 검사 가능일 및 가능 여부 계산
        LocalDateTime nextEligibleAt = latestExam.getNextEligibleAt();
        boolean isExamEligible = !LocalDateTime.now().isBefore(nextEligibleAt);

        // 2) 진행 상황 (진행 중인 검사의 비디오 개수)
        int examProgress = (latestExam.getExamStatus() == ExamStatus.IN_PROGRESS)
                ? videoRepository.countByExam(latestExam)
                : 0;

        // 3) 기존 완료된 검사 존재 여부
        boolean hasPreviousExam = (latestExam.getExamStatus() == ExamStatus.COMPLETED)
                || examRepository.existsByChild_ChildIdAndExamStatus(childId, ExamStatus.COMPLETED);

        return Optional.of(new ExamSummaryResponse(isExamEligible, examProgress, hasPreviousExam, nextEligibleAt));
    }
}
