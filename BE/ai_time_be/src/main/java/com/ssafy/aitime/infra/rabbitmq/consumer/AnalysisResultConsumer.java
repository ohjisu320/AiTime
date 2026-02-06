package com.ssafy.aitime.infra.rabbitmq.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import com.ssafy.aitime.domain.exam.service.AdosCalculationService;
import com.ssafy.aitime.domain.exam.service.ResultSaveService;
import com.ssafy.aitime.infra.rabbitmq.dto.message.AnalysisResultMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Slf4j
@Component
public class AnalysisResultConsumer {

    private final ObjectMapper objectMapper;
    private final VideoRepository videoRepository;
    private final ResultSaveService resultSaveService;
    private final AdosCalculationService adosCalculationService;

    public AnalysisResultConsumer(
            @Qualifier("rabbitObjectMapper") ObjectMapper objectMapper,
            VideoRepository videoRepository,
            ResultSaveService resultSaveService,
            AdosCalculationService adosCalculationService) {
        this.objectMapper = objectMapper;
        this.videoRepository = videoRepository;
        this.resultSaveService = resultSaveService;
        this.adosCalculationService = adosCalculationService;
    }

    @RabbitListener(queues = "analysis.resp")
    @Transactional
    public void handleAnalysisResult(String message) {
        try {
            // 1. JSON 파싱
            AnalysisResultMessage result = objectMapper.readValue(
                    message, AnalysisResultMessage.class);

            log.info("✅ [1-RabbitMQ] 분석 결과 수신 - examId: {}, videoId: {}, videoType: {}, status: {}",
                    result.getExamId(), result.getVideoId(), result.getVideoType(), result.getStatus());

            // 2. Video 조회 (videoId로 직접 조회)
            Video video = videoRepository.findById(result.getVideoId())
                    .orElseThrow(() -> new IllegalStateException(
                            "Video not found - videoId: " + result.getVideoId()));

            // 3. Video 정합성 체크
            if (!video.getExam().getExamId().equals(result.getExamId())) {
                log.error("❌ [2-RabbitMQ] ExamId 불일치 - expected: {}, actual: {}",
                        video.getExam().getExamId(), result.getExamId());
                return;
            }

            if (!video.getVideoType().name().equals(result.getVideoType())) {
                log.error("❌ [3-RabbitMQ] VideoType 불일치 - expected: {}, actual: {}",
                        video.getVideoType(), result.getVideoType());
                return;
            }

            // 4. 멱등성 체크 (이미 처리된 메시지 무시)
            if (video.getAnalysisStatus() ==
                    com.ssafy.aitime.domain.exam.entity.enums.AnalysisStatus.SUCCESS) {
                log.warn("⚠️ [4-RabbitMQ] 이미 처리된 메시지 무시 - videoId: {}", video.getVideoId());
                return;
            }

            // 5. 결과에 따라 처리
            if (isSuccess(result)) {
                handleSuccess(video, result);
                tryCalculateAdos(video.getExam().getExamId());
            } else {
                handleFailure(video, result);
            }

            // 명시적 flush 추가
            videoRepository.flush();

        } catch (Exception e) {
            log.error("❌ [5-RabbitMQ] 분석 결과 수신 처리 실패", e);
            // TODO: Dead Letter Queue로 이동 또는 재시도 로직
        }
    }

    /**
     * 분석 성공 여부 확인
     */
    private boolean isSuccess(AnalysisResultMessage result) {
        return "SUCCESS".equalsIgnoreCase(result.getStatus());
    }

    /**
     * 분석 성공 처리
     */
    private void handleSuccess(Video video, AnalysisResultMessage result) {
        // Video 상태 업데이트
        video.completeAnalysis();
        videoRepository.save(video);

        // Trial/Event 저장
        resultSaveService.saveResult(video, result);

        log.info("✅ [6-RabbitMQ] 영상 분석 성공 처리 완료 - videoId: {}, videoType: {}",
                video.getVideoId(), result.getVideoType());
    }

    /**
     * 분석 실패 처리
     */
    private void handleFailure(Video video, AnalysisResultMessage result) {
        String errorMessage = String.format("❌ [7-RabbitMQ] 영상 분석 실패 - status: %s, analyzedAt: %s",
                result.getStatus(),
                result.getAnalyzedAt());

        video.failAnalysis(errorMessage);
        videoRepository.save(video);

        log.warn("⚠️ [8-RabbitMQ] 영상 분석 실패 처리 완료 - videoId: {}, reason: {}",
                video.getVideoId(), errorMessage);
    }

    /**
     * ADOS 계산 시도
     *
     * 4개 영상이 모두 분석 완료되면 ADOS 계산
     */
    private void tryCalculateAdos(UUID examId) {
        try {
            log.info(">>> [9-RabbitMQ] ADOS 계산 시도 - examId: {}", examId);
            adosCalculationService.calculateAndSaveAdos(examId);
        } catch (Exception e) {
            log.error("❌ [10-RabbitMQ] ADOS 계산 실패 - examId: {}", examId, e);
            // ADOS 계산 실패해도 메인 플로우는 계속 진행
        }
    }
}