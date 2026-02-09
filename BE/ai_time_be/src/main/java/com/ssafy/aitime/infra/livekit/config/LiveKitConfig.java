package com.ssafy.aitime.infra.livekit.config;

import io.livekit.server.RoomServiceClient;
import io.livekit.server.EgressServiceClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
public class LiveKitConfig {

    @Value("${livekit.url}")
    private String livekitUrl;

    @Value("${livekit.api-key}")
    private String apiKey;

    @Value("${livekit.api-secret}")
    private String apiSecret;

    @Bean
    public RoomServiceClient roomServiceClient() {
        log.info("Initializing LiveKit RoomServiceClient with URL: {}", livekitUrl);
        return RoomServiceClient.create(livekitUrl, apiKey, apiSecret);
    }

    @Bean
    public EgressServiceClient egressServiceClient() {
        log.info("Initializing LiveKit EgressServiceClient");
        return EgressServiceClient.create(livekitUrl, apiKey, apiSecret);
    }
}
