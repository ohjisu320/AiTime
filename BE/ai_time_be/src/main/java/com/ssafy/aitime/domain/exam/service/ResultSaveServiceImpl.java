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
            case 1 -> savePoseImitationResult(video, metrics, result.getAdos());
            case 2 -> saveSpeechImitationResult(video, metrics, result.getAdos());
            case 3 -> saveNameFacingResult(video, metrics, result.getAdos());
            case 4 -> saveNameNonFacingResult(video, metrics, result.getAdos());
            default -> throw new IllegalArgumentException("Invalid taskNo: " + taskNo);
        }

        log.info("✅ 결과 저장 완료 - videoId: {}, taskNo: {}", video.getVideoId(), taskNo);
    }

    // ========== Task 1: 동작 모방행동 (PoseImitation) ==========
    private void savePoseImitationResult(Video video, List<AnalysisResultMessage.TrialMetric> metrics,
                                         AnalysisResultMessage.AdosData adosData) {
        // Trial 저장 (ADOS 원본 데이터 포함)
        PoseImitationTrial trial = PoseImitationTrial.builder()
                .video(video)
                .adosB6(convertToString(adosData.getB6()))       // TRUE/FALSE
                .adosA8(convertToString(adosData.getA8()))       // 0-3
                .adosB18(convertToString(adosData.getB18()))     // TRUE/FALSE
                .build();
        poseImitationTrialRepository.save(trial);

        // Event 저장 (시도별 상세)
        for (AnalysisResultMessage.TrialMetric metric : metrics) {
            PoseImitationEvent event = PoseImitationEvent.builder()
                    .poseImitationTrial(trial)
                    .trialIndex(metric.getTrialIndex())
                    .actionType(metric.getActionType())
                    .success(metric.getSuccess())
                    .similarityScore(metric.getSimilarityScore())
                    .parentStartTime(metric.getParentStartTime())
                    .parentEndTime(metric.getParentEndTime())
                    .childStartTime(metric.getChildStartTime())
                    .childEndTime(metric.getChildEndTime())
                    .latencyS(metric.getLatencyS())
                    .durationS(metric.getDurationS())
                    .attentionRatio(metric.getAttentionRatio())
                    .build();
            poseImitationEventRepository.save(event);
        }

        log.debug("동작 모방행동 저장 완료 - trial: {}, events: {}", trial.getPoseImitationTrialId(), metrics.size());
    }

    // ========== Task 2: 발화 모방행동 (SpeechImitation) ==========
    private void saveSpeechImitationResult(Video video, List<AnalysisResultMessage.TrialMetric> metrics,
                                           AnalysisResultMessage.AdosData adosData) {
        // Trial 저장 (ADOS 원본 데이터 포함)
        SpeechImitationTrial trial = SpeechImitationTrial.builder()
                .video(video)
                .adosA3(convertToString(adosData.getA3()))       // 0-3
                .adosB18(convertToString(adosData.getB18()))     // TRUE/FALSE
                .build();
        speechImitationTrialRepository.save(trial);

        // Event 저장 (시도별 상세)
        for (AnalysisResultMessage.TrialMetric metric : metrics) {
            SpeechImitationEvent event = SpeechImitationEvent.builder()
                    .speechImitationTrial(trial)
                    .trialIndex(metric.getTrialIndex())
                    .trialStartS(metric.getTrialStartS())
                    .trialEndS(metric.getTrialEndS())
                    .stimulusId(metric.getStimulusId())
                    .stimulusText(metric.getStimulusText())
                    .responseDetected(metric.getResponseDetected())
                    .latencyS(metric.getLatencyS())
                    .success(metric.getSuccess())
                    .failureReason(metric.getFailureReason())
                    .freqAbnormal(metric.getFreqAbnormal())
                    .build();
            speechImitationEventRepository.save(event);
        }

        log.debug("발화 모방행동 저장 완료 - trial: {}, events: {}", trial.getSpeechImitationTrialId(), metrics.size());
    }

    // ========== Task 3: 대면 호명반응 (NameFacing) ==========
    private void saveNameFacingResult(Video video, List<AnalysisResultMessage.TrialMetric> metrics,
                                      AnalysisResultMessage.AdosData adosData) {
        // Trial 저장 (ADOS 원본 데이터 포함)
        NameFacingTrial trial = NameFacingTrial.builder()
                .video(video)
                .adosB1(convertToString(adosData.getB1()))       // 0-3
                .adosB4(convertToString(adosData.getB4()))       // 0-3
                .adosB6(convertToString(adosData.getB6()))       // TRUE/FALSE
                .adosB18(convertToString(adosData.getB18()))     // TRUE/FALSE
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
                    .emotion(metric.getEmotion())
                    .build();
            nameFacingEventRepository.save(event);
        }

        log.debug("대면 호명반응 저장 완료 - trial: {}, events: {}", trial.getNameFacingTrialId(), metrics.size());
    }

    // ========== Task 4: 비대면 호명반응 (NameNonFacing) ==========
    private void saveNameNonFacingResult(Video video, List<AnalysisResultMessage.TrialMetric> metrics,
                                         AnalysisResultMessage.AdosData adosData) {
        // Trial 저장 (ADOS 원본 데이터 포함)
        NameNonFacingTrial trial = NameNonFacingTrial.builder()
                .video(video)
                .adosB7(convertToString(adosData.getB7()))       // 0-3
                .adosB18(convertToString(adosData.getB18()))     // TRUE/FALSE
                .build();
        nameNonFacingTrialRepository.save(trial);

        // Event 저장 (시도별 상세)
        for (AnalysisResultMessage.TrialMetric metric : metrics) {
            NameNonFacingEvent event = NameNonFacingEvent.builder()
                    .nameNonFacingTrial(trial)
                    .trialIndex(metric.getTrialIndex())
                    .success(metric.getSuccess())
                    .latencyS(metric.getLatencyS())
                    .triggerStartS(metric.getTriggerStartS())
                    .triggerEndS(metric.getTriggerEndS())
                    .triggerText(metric.getTriggerText())
                    .voiceDetected(metric.getVoiceDetected())
                    .voiceStartS(metric.getVoiceStartS())
                    .voiceEndS(metric.getVoiceEndS())
                    .voiceDurationS(metric.getVoiceDurationS())
                    .voiceConfidence(metric.getVoiceConfidence())
                    .gazeMatch(metric.getGazeMatch())
                    .gazeDurationS(metric.getGazeDurationS())
                    .headYawDeg(metric.getHeadYawDeg())
                    .headPitchDeg(metric.getHeadPitchDeg())
                    .build();
            nameNonFacingEventRepository.save(event);
        }

        log.debug("비대면 호명반응 저장 완료 - trial: {}, events: {}", trial.getNameNonFacingTrialId(), metrics.size());
    }

    /**
     * ADOS 데이터를 String으로 변환 (원본 데이터 저장용)
     * API에서 Boolean 또는 Integer로 올 수 있음
     */
    private String convertToString(Object value) {
        if (value == null) {
            return null;
        }

        if (value instanceof Boolean) {
            return ((Boolean) value) ? "TRUE" : "FALSE";
        }

        return String.valueOf(value);
    }
}