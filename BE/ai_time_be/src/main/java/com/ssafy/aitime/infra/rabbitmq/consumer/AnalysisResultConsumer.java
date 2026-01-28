package com.ssafy.aitime.infra.rabbitmq.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
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

    public AnalysisResultConsumer(
            @Qualifier("rabbitObjectMapper") ObjectMapper objectMapper,
            VideoRepository videoRepository,
            ResultSaveService resultSaveService) {
        this.objectMapper = objectMapper;
        this.videoRepository = videoRepository;
        this.resultSaveService = resultSaveService;
    }

    @RabbitListener(queues = "analysis.resp")
    @Transactional
    public void handleAnalysisResult(String message) {
        try {
            // 1. JSON 파싱
            AnalysisResultMessage result = objectMapper.readValue(
                    message, AnalysisResultMessage.class);

            log.info("✅ 분석 결과 수신 - jobId: {}, taskNo: {}, status: {}",
                    result.getJobId(), result.getTaskNo(), result.getStatus());

            // 2. Video 조회
            UUID examId = UUID.fromString(result.getJobId());
            Video video = findVideoByExamIdAndTaskNo(examId, result.getTaskNo());

            // 3. 멱등성 체크 (이미 처리된 메시지 무시)
            if (video.getAnalysisStatus() ==
                    com.ssafy.aitime.domain.exam.entity.enums.AnalysisStatus.SUCCESS) {
                log.warn("⚠️ 이미 처리된 메시지 무시 - videoId: {}", video.getVideoId());
                return;
            }

            // 4. 결과에 따라 처리
            if (result.isSuccess()) {
                handleSuccess(video, result);
            } else {
                handleFailure(video, result);
            }

            // 명시적 flush 추가
            videoRepository.flush();

        } catch (Exception e) {
            log.error("❌ 분석 결과 처리 실패", e);
            // TODO: Dead Letter Queue로 이동 또는 재시도 로직
        }
    }

    private Video findVideoByExamIdAndTaskNo(UUID examId, Integer taskNo) {
        var videoType = mapTaskNoToVideoType(taskNo);
        return videoRepository.findByExamExamIdAndVideoType(examId, videoType)
                .orElseThrow(() -> new IllegalStateException(
                        "Video not found - examId: " + examId + ", taskNo: " + taskNo));
    }

    private com.ssafy.aitime.domain.exam.entity.enums.VideoType mapTaskNoToVideoType(Integer taskNo) {
        return switch (taskNo) {
            case 1 -> VideoType.POSE_IMITATION;      // task1: 동작 모방행동
            case 2 -> VideoType.SPEECH_IMITATION;    // task2: 발화 모방행동
            case 3 -> VideoType.NAME_FACING;         // task3: 대면 호명반응
            case 4 -> VideoType.NAME_NON_FACING;     // task4: 비대면 호명반응
            default -> throw new IllegalArgumentException("Invalid taskNo: " + taskNo);
        };
    }

    private void handleSuccess(Video video, AnalysisResultMessage result) {
        // Video 상태 업데이트
        video.completeAnalysis();
        videoRepository.save(video);

        // Trial/Event 저장
        resultSaveService.saveResult(video, result);

        log.info("✅ 분석 성공 처리 완료 - videoId: {}", video.getVideoId());
    }

    private void handleFailure(Video video, AnalysisResultMessage result) {
        String errorMessage = result.getError() != null
                ? result.getError().getCode() + ": " + result.getError().getMessage()
                : "Unknown error";

        video.failAnalysis(errorMessage);
        videoRepository.save(video);

        log.warn("⚠️ 분석 실패 처리 완료 - videoId: {}, reason: {}",
                video.getVideoId(), errorMessage);
    }
}
