package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.child.entity.enums.ChildHomeStatus;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryDTO;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import com.ssafy.aitime.domain.hospital.service.HospitalService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ExamServiceImpl implements ExamService {

    private final ExamRepository examRepository;
    private final VideoRepository videoRepository;
    private final HospitalService hospitalService;

    @Override
    @Transactional(readOnly = true)
    public ExamSummaryDTO getExamSummaryForChild(UUID childId) {
        // 1. 병원 연동 여부 확인
        boolean hasLinkedHospital = hospitalService.hasLinkedHospital(childId);
        if (!hasLinkedHospital) {
            return ExamSummaryDTO.empty(); // NEED_HOSPITAL
        }

        // 2. 가장 최신 검사 기록 조회
        Optional<Exam> latestExamOpt = examRepository.findFirstByChild_ChildIdOrderByCreatedAtDesc(childId);

        // 3. 검사 기록이 없으면 AVAILABLE 상태
        if (latestExamOpt.isEmpty()) {
            return new ExamSummaryDTO(
                    ChildHomeStatus.AVAILABLE,
                    0,
                    null,
                    null,
                    null
            );
        }

        Exam latestExam = latestExamOpt.get();

        // 4. 상태 계산
        ChildHomeStatus status = calculateExamStatus(latestExam, childId);

        // 5. 업로드된 비디오 개수 계산
        int examProgress = (latestExam.getExamStatus() == ExamStatus.IN_PROGRESS)
                ? countUploadedVideos(latestExam)
                : 0;

        // 6. DTO 조립
        return new ExamSummaryDTO(
                status,
                examProgress,
                latestExam.getExamStartedAt() != null ? latestExam.getExamStartedAt().toLocalDate() : null,
                latestExam.getNextEligibleAt() != null ? latestExam.getNextEligibleAt().toLocalDate() : null,
                latestExam.getDraftExpiresAt()
        );
    }

    /**
     * 검사 상태를 계산하는 핵심 로직
     */
    private ChildHomeStatus calculateExamStatus(Exam exam, UUID childId) {
        LocalDateTime now = LocalDateTime.now();
        ExamStatus examStatus = exam.getExamStatus();
        LocalDateTime draftExpiresAt = exam.getDraftExpiresAt();
        LocalDateTime nextEligibleAt = exam.getNextEligibleAt();

        // Case 1: 검사 완료 상태
        if (examStatus == ExamStatus.COMPLETED) {
            // 다음 검사 가능일이 지났으면 AVAILABLE
            if (nextEligibleAt == null || !now.isBefore(nextEligibleAt)) {
                return ChildHomeStatus.AVAILABLE;
            }
            // 아직 3개월이 안 지났으면 COOLDOWN
            return ChildHomeStatus.COOLDOWN;
        }

        // Case 2: 검사 진행 중 상태 (IN_PROGRESS)
        if (examStatus == ExamStatus.IN_PROGRESS) {
            // 2-1. draftExpiresAt이 null이면 아직 시작 전 (첫 비디오 업로드 전)
            if (draftExpiresAt == null) {
                return ChildHomeStatus.AVAILABLE;
            }

            // 2-2. draftExpiresAt이 지났으면 만료됨
            if (now.isAfter(draftExpiresAt)) {
                return ChildHomeStatus.AVAILABLE_EXPIRED;
            }

            // 2-3. 진행 중
            return ChildHomeStatus.IN_PROGRESS;
        }

        // Default: AVAILABLE
        return ChildHomeStatus.AVAILABLE;
    }

    /**
     * 업로드 완료된 비디오 개수 카운트 (UPLOADED 상태만)
     */
    private int countUploadedVideos(Exam exam) {
        List<Video> videos = videoRepository.findByExam(exam);
        return (int) videos.stream()
                .filter(v -> v.getVideoStatus() == VideoStatus.UPLOADED)
                .count();
    }
}
