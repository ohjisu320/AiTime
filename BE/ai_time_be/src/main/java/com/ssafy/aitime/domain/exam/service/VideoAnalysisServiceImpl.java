package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryResponse;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class VideoAnalysisServiceImpl implements VideoAnalysisService {

    private final ExamRepository examRepository;
    private final VideoRepository videoRepository;
    private final AnalysisPublisher analysisPublisher;

    @Override
    @Transactional
    public void requestAnalysis(UUID examId) {
        // 1. Exam 조회
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new IllegalArgumentException("Exam not found: " + examId));

        // 2. 해당 Exam의 모든 Video 조회
        List<Video> videos = videoRepository.findByExamExamId(examId);

        if (videos.size() != 4) {
            throw new IllegalStateException(
                    "Exam must have exactly 4 videos, but found: " + videos.size());
        }

        // 3. 아이의 개월 수 계산
        Long ageMonths = calculateAgeMonths(exam);

        // 4. 각 영상에 대해 분석 요청
        for (Video video : videos) {
            requestVideoAnalysis(video, ageMonths);
        }

        // 5. 마지막 비디오 녹화 시간 찾기 (가장 최근 recordedAt)
        LocalDateTime lastRecordedAt = videos.stream()
                .map(Video::getRecordedAt)
                .filter(recordedAt -> recordedAt != null)
                .max(LocalDateTime::compareTo)
                .orElse(null);

        // 6. Exam 상태를 COMPLETED로 변경 및 다음 검사 가능일 설정
        exam.markSubmitted(lastRecordedAt);
        examRepository.save(exam);

        log.info("✅ 검사 분석 요청 완료 - examId: {}, videoCount: {}, nextEligibleAt: {}",
                examId, videos.size(), exam.getNextEligibleAt());
    }

    @Override
    @Transactional
    public void requestSingleVideoAnalysis(UUID videoId) {
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new IllegalArgumentException("Video not found: " + videoId));

        Long ageMonths = calculateAgeMonths(video.getExam());
        requestVideoAnalysis(video, ageMonths);
    }

    private void requestVideoAnalysis(Video video, Long ageMonths) {
        // 1. 분석 가능 여부 확인
        if (!video.canRequestAnalysis()) {
            log.warn("⚠️ 분석 요청 불가 - videoId: {}, status: {}",
                    video.getVideoId(), video.getAnalysisStatus());
            return;
        }

        // 2. Video 상태 업데이트
        video.requestAnalysis("v1.0"); // 모델 버전
        videoRepository.save(video);

        // 3. RabbitMQ로 메시지 발행
        AnalysisRequestMessage message = AnalysisRequestMessage.from(video, ageMonths);
        analysisPublisher.publishAnalysisRequest(message);

        log.info("✅ 영상 분석 요청 - videoId: {}, taskNo: {}",
                video.getVideoId(), message.getTaskNo());
    }

    /**
     * 아이의 개월 수 계산
     */
    private Long calculateAgeMonths(Exam exam) {
        LocalDate birthDate = exam.getChild().getBirthdate();

        if (birthDate == null) {
            log.warn("⚠️ Child의 birthDate가 null입니다. examId: {}", exam.getExamId());
            return 0L;
        }

        LocalDate now = LocalDate.now();
        Period period = Period.between(birthDate, now);

        // 연도와 월을 합산하여 전체 개월 수 계산
        long totalMonths = period.getYears() * 12L + period.getMonths();

        log.debug("아이 개월 수 계산 - birthDate: {}, 현재: {}, 개월수: {}",
                birthDate, now, totalMonths);

        return totalMonths;
    }
}
