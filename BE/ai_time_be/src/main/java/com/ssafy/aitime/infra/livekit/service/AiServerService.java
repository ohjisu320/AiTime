package com.ssafy.aitime.infra.livekit.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiServerService {

    private final WebClient webClient;

    @Value("${ai-server.base-url}")
    private String aiServerBaseUrl;

    @Value("${ai-server.start-analysis-endpoint}")
    private String startAnalysisEndpoint;

    @Value("${ai-server.timeout}")
    private long timeout;

    /**
     * AI 서버에 분석 시작 명령 전송
     */
    public Mono<Void> startAnalysis(String roomName, String aiToken, Long sessionId) {
        String url = aiServerBaseUrl + startAnalysisEndpoint;

        Map<String, Object> requestBody = Map.of(
                "room_name", roomName,
                "token", aiToken,
                "session_id", sessionId,
                "participant_name", "ai-agent-" + sessionId
        );

        log.info("Sending start analysis request to AI server: {}", url);

        return webClient.post()
                .uri(url)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(Void.class)
                .timeout(Duration.ofMillis(timeout))
                .doOnSuccess(response ->
                        log.info("Successfully triggered AI analysis for room: {}", roomName))
                .doOnError(error ->
                        log.error("Failed to start AI analysis for room: {}", roomName, error));
    }
}