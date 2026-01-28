package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.assessment.*;
import com.ssafy.aitime.domain.exam.repository.assessment.*;
import com.ssafy.aitime.infra.rabbitmq.dto.message.AnalysisResultMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class ResultSaveServiceImpl implements ResultSaveService {

    private final NameFacingTrialRepository nameFacingTrialRepository;
    private final NameFacingEventRepository nameFacingEventRepository;
    private final SpeechImitationTrialRepository speechImitationTrialRepository;
    private final SpeechImitationEventRepository speechImitationEventRepository;
    private final PoseImitationTrialRepository poseImitationTrialRepository;
    private final PoseImitationEventRepository poseImitationEventRepository;
    private final NameNonFacingTrialRepository nameNonFacingTrialRepository;
    private final NameNonFacingEventRepository nameNonFacingEventRepository;

    /**
     * 분석 결과를 DB에 저장
     */
    @Override
    @Transactional
    public void saveResult(Video video, AnalysisResultMessage result) {
        Integer taskNo = result.getTaskNo();
        List<AnalysisResultMessage.TrialMetric> metrics = result.getMetrics().getPerTrial();

        switch (taskNo) {
            case 1 -> savePoseImitationResult(video, metrics);
            case 2 -> saveSpeechImitationResult(video, metrics);
            case 3 -> saveNameFacingResult(video, metrics);
            case 4 -> saveNameNonFacingResult(video, metrics);
            default -> throw new IllegalArgumentException("Invalid taskNo: " + taskNo);
        }

        log.info("✅ 결과 저장 완료 - videoId: {}, taskNo: {}", video.getVideoId(), taskNo);
    }

    // ========== Task 1: 대면 호명반응 ==========
    private void saveNameFacingResult(Video video, List<AnalysisResultMessage.TrialMetric> metrics) {
        // 집계 정보 계산
        int totalCount = metrics.size();
        long successCount = metrics.stream()
                .filter(m -> Boolean.TRUE.equals(m.getSuccess()))
                .count();
        double successRate = totalCount > 0 ? (double) successCount / totalCount : 0.0;

        // Trial 저장
        NameFacingTrial trial = NameFacingTrial.builder()
                .video(video)
                .totalCallCount(totalCount)
                .successCount((int) successCount)
                .successRate(successRate)
                .build();
        nameFacingTrialRepository.save(trial);

        // Event 저장 (시도별 상세)
        for (AnalysisResultMessage.TrialMetric metric : metrics) {
            NameFacingEvent event = NameFacingEvent.builder()
                    .nameFacingTrial(trial)
                    .trialIndex(metric.getTrialIndex())
                    .trialStartS(metric.getTrialStartS())
                    .trialEndS(metric.getTrialEndS())
                    .success(metric.getSuccess())
                    .latencyS(metric.getLatencyS())
                    .gazeDurationS(metric.getGazeDurationS())
                    .build();
            nameFacingEventRepository.save(event);
        }

        log.debug("대면 호명반응 저장 완료 - trial: {}, events: {}", trial.getNameFacingTrialId(), metrics.size());
    }

    // ========== Task 2: 발화 모방행동 ==========
    private void saveSpeechImitationResult(Video video, List<AnalysisResultMessage.TrialMetric> metrics) {
        // SpeechImitationTrial은 stimulus 정보를 가지고 있어야 하므로
        // metrics에서 첫 번째 항목의 정보를 사용 (또는 별도 처리 필요)

        for (AnalysisResultMessage.TrialMetric metric : metrics) {
            // Trial 저장 (stimulus별로 생성)
            SpeechImitationTrial trial = SpeechImitationTrial.builder()
                    .video(video)
                    .stimulusId(metric.getStimulusId())
                    .stimulusText(metric.getStimulusText())
                    .build();
            speechImitationTrialRepository.save(trial);

            // Event 저장
            SpeechImitationEvent event = SpeechImitationEvent.builder()
                    .speechImitationTrial(trial)
                    .trialIndex(metric.getTrialIndex())
                    .responseDetected(metric.getResponseDetected())
                    .latencyS(metric.getLatencyS())
                    .success(metric.getSuccess())
                    .failureReason(metric.getFailureReason())
                    .build();
            speechImitationEventRepository.save(event);
        }

        log.debug("발화 모방행동 저장 완료 - events: {}", metrics.size());
    }

    // ========== Task 3: 동작 모방행동 ==========
    private void savePoseImitationResult(Video video, List<AnalysisResultMessage.TrialMetric> metrics) {
        // 집계 정보 계산
        int totalCount = metrics.size();
        long successCount = metrics.stream()
                .filter(m -> Boolean.TRUE.equals(m.getSuccess()))
                .count();
        double successRate = totalCount > 0 ? (double) successCount / totalCount : 0.0;

        // Trial 저장
        PoseImitationTrial trial = PoseImitationTrial.builder()
                .video(video)
                .totalTrialCount(totalCount)
                .successCount((int) successCount)
                .successRate(successRate)
                .build();
        poseImitationTrialRepository.save(trial);

        // Event 저장 (시도별 상세)
        for (AnalysisResultMessage.TrialMetric metric : metrics) {
            PoseImitationEvent event = PoseImitationEvent.builder()
                    .poseImitationTrial(trial)
                    .trialIndex(metric.getTrialIndex())
                    .responseSuccess(metric.getSuccess())
                    .similarityScore(metric.getSimilarityScore())
                    .responseLatencyS(metric.getLatencyS())
                    .durationS(metric.getDurationS())
                    .attentionRatio(metric.getAttentionRatio())
                    .build();
            poseImitationEventRepository.save(event);
        }

        log.debug("동작 모방행동 저장 완료 - trial: {}, events: {}", trial.getPoseImitationTrialId(), metrics.size());
    }

    // ========== Task 4: 비대면 호명반응 ==========
    private void saveNameNonFacingResult(Video video, List<AnalysisResultMessage.TrialMetric> metrics) {
        // 집계 정보 계산
        int totalCount = metrics.size();
        long successCount = metrics.stream()
                .filter(m -> Boolean.TRUE.equals(m.getSuccess()))
                .count();
        double successRate = totalCount > 0 ? (double) successCount / totalCount : 0.0;

        // Trial 저장
        NameNonFacingTrial trial = NameNonFacingTrial.builder()
                .video(video)
                .totalCallCount(totalCount)
                .successCount((int) successCount)
                .successRate(successRate)
                .build();
        nameNonFacingTrialRepository.save(trial);

        // Event 저장 (시도별 상세)
        for (AnalysisResultMessage.TrialMetric metric : metrics) {
            NameNonFacingEvent event = NameNonFacingEvent.builder()
                    .nameNonFacingTrial(trial)
                    .trialIndex(metric.getTrialIndex())
                    .responseSuccess(metric.getSuccess())
                    .latencyS(metric.getLatencyS())
                    .gazeDurationS(metric.getGazeDurationS())
                    .headYawDeg(metric.getHeadYawDeg())
                    .headPitchDeg(metric.getHeadPitchDeg())
                    .build();
            nameNonFacingEventRepository.save(event);
        }

        log.debug("비대면 호명반응 저장 완료 - trial: {}, events: {}", trial.getNameNonFacingTrialId(), metrics.size());
    }
}
