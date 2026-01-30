package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.ChildHomeStatus;
import com.ssafy.aitime.domain.exam.dto.response.ExamStartResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryDTO;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.exception.ExamNotEligibleException;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import com.ssafy.aitime.domain.hospital.service.HospitalService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Slf4j
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
        ChildHomeStatus status = calculateExamStatus(latestExam);

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

    @Override
    @Transactional
    public ExamStartResponse createExam(Child child) {
        UUID childId = child.getChildId();

        // 1. 현재 검사 상태 확인
        ExamSummaryDTO examSummary = getExamSummaryForChild(childId);
        ChildHomeStatus currentStatus = examSummary.childHomeStatus();

        // 2. 검사 시작 가능 상태인지 확인 (AVAILABLE 또는 AVAILABLE_EXPIRED만 허용)
        if (!(currentStatus == ChildHomeStatus.AVAILABLE
                || currentStatus == ChildHomeStatus.AVAILABLE_EXPIRED)) {
            throw new ExamNotEligibleException();
        }

        // 3. AVAILABLE_EXPIRED인 경우, 기존 IN_PROGRESS 검사를 삭제 (만료된 데이터 정리)
        if (currentStatus == ChildHomeStatus.AVAILABLE_EXPIRED) {
            examRepository.findFirstByChild_ChildIdOrderByCreatedAtDesc(childId)
                    .ifPresent(examRepository::delete);
        }

        // 4. 새로운 Exam 엔티티 생성
        Exam newExam = Exam.builder()
                .child(child)
                .examStatus(ExamStatus.IN_PROGRESS)
                .submitted(false)
                .examStartedAt(null)  // 첫 비디오 업로드 시 설정됨
                .nextEligibleAt(null) // 검사 완료 시 설정됨
                .draftExpiresAt(null) // 첫 비디오 업로드 시 설정됨
                .completedAt(null)
                .build();

        Exam savedExam = examRepository.save(newExam);

        log.info("새로운 검사 생성 - examId: {}, childId: {}",
                savedExam.getExamId(), childId);

        return ExamStartResponse.of(
                savedExam.getExamId(),
                childId,
                savedExam.getExamStatus()
        );
    }

    /**
     * 검사 상태를 계산하는 핵심 로직
     */
    private ChildHomeStatus calculateExamStatus(Exam exam) {
        LocalDateTime now = LocalDateTime.now();
        ExamStatus examStatus = exam.getExamStatus();
        LocalDateTime draftExpiresAt = exam.getDraftExpiresAt();
        LocalDateTime nextEligibleAt = exam.getNextEligibleAt();

        // Case 1: 검사 완료 상태
        if (examStatus == ExamStatus.COMPLETED) {
            if (nextEligibleAt == null || !now.isBefore(nextEligibleAt)) {
                return ChildHomeStatus.AVAILABLE;
            }
            return ChildHomeStatus.COOLDOWN;
        }

        // Case 2: 검사 진행 중 상태 (IN_PROGRESS)
        if (examStatus == ExamStatus.IN_PROGRESS) {
            // ✅ 수정: draftExpiresAt이 null이면 검사 생성 직후
            if (draftExpiresAt == null) {
                return ChildHomeStatus.IN_PROGRESS;  // ✅ 변경
            }

            // draftExpiresAt이 지났으면 만료
            if (now.isAfter(draftExpiresAt)) {
                return ChildHomeStatus.AVAILABLE_EXPIRED;
            }

            // 진행 중
            return ChildHomeStatus.IN_PROGRESS;
        }

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
