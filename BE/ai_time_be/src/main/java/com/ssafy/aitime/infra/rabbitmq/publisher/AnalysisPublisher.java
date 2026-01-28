package com.ssafy.aitime.infra.rabbitmq.publisher;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.aitime.infra.rabbitmq.dto.message.AnalysisRequestMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class AnalysisPublisher {

    private final RabbitTemplate rabbitTemplate;
    private final ObjectMapper objectMapper;

    public AnalysisPublisher(
            RabbitTemplate rabbitTemplate,
            @Qualifier("rabbitObjectMapper") ObjectMapper objectMapper) {
        this.rabbitTemplate = rabbitTemplate;
        this.objectMapper = objectMapper;
    }

    /**
     * AI 서버로 분석 요청 메시지 발행
     */
    public void publishAnalysisRequest(AnalysisRequestMessage message) {
        try {
            String queueName = message.getQueueName();
            String jsonMessage = objectMapper.writeValueAsString(message);

            rabbitTemplate.convertAndSend(queueName, jsonMessage);

            log.info("✅ 분석 요청 발행 완료 - jobId: {}, taskNo: {}, queue: {}",
                    message.getJobId(), message.getTaskNo(), queueName);

        } catch (Exception e) {
            log.error("❌ 분석 요청 발행 실패 - jobId: {}, taskNo: {}",
                    message.getJobId(), message.getTaskNo(), e);
            throw new RuntimeException("메시지 발행 실패", e);
        }
    }
}
