package com.ssafy.aitime.infra.livekit.service;

import io.livekit.server.*;
import livekit.LivekitModels.Room;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class LiveKitService {

    private final RoomServiceClient roomServiceClient;

    @Value("${livekit.api-key}")
    private String apiKey;

    @Value("${livekit.api-secret}")
    private String apiSecret;

    /**
     * LiveKit Room 생성
     */
    public Room createRoom(String roomName) {
        try {
            // createRoom 메서드가 개별 파라미터를 받음
            Room room = roomServiceClient.createRoom(
                    roomName,           // name
                    300,                // emptyTimeout (5분)
                    2,                  // maxParticipants
                    null,               // nodeId
                    null,               // metadata
                    null,               // minPlayoutDelay
                    null,               // maxPlayoutDelay
                    null,               // syncStreams
                    null                // departureTimeout
            ).execute().body();

            log.info("Created LiveKit room: {}", roomName);
            return room;

        } catch (Exception e) {
            log.error("Failed to create room: {}", roomName, e);
            throw new RuntimeException("Room creation failed", e);
        }
    }

    /**
     * 사용자용 Access Token 생성 (비디오 송출 권한)
     */
    public String generateUserToken(String roomName, String participantName) {
        AccessToken token = new AccessToken(apiKey, apiSecret);
        token.setName(participantName);
        token.setIdentity(participantName);

        // VideoGrants 빌더 패턴 사용
        token.addGrants(new RoomJoin(true));
        token.addGrants(new RoomName(roomName));
        token.addGrants(new CanPublish(true));
        token.addGrants(new CanSubscribe(true));
        token.addGrants(new CanPublishData(true));

        String jwt = token.toJwt();
        log.info("Generated user token for participant: {} in room: {}", participantName, roomName);
        return jwt;
    }

    /**
     * AI용 Access Token 생성 (비디오 수신 + 데이터 채널 전송 권한)
     */
    public String generateAiToken(String roomName, String aiParticipantName) {
        AccessToken token = new AccessToken(apiKey, apiSecret);
        token.setName(aiParticipantName);
        token.setIdentity(aiParticipantName);

        // AI는 비디오 송출 안 함, 수신만
        token.addGrants(new RoomJoin(true));
        token.addGrants(new RoomName(roomName));
        token.addGrants(new CanPublish(false));        // 비디오 송출 안 함
        token.addGrants(new CanSubscribe(true));       // 비디오 수신
        token.addGrants(new CanPublishData(true));     // 데이터 채널 전송

        String jwt = token.toJwt();
        log.info("Generated AI token for participant: {} in room: {}", aiParticipantName, roomName);
        return jwt;
    }

    /**
     * Room 이름 생성 (UUID 기반)
     */
    public String generateRoomName(Long userId, String prefix) {
        return String.format("%s_%d_%s", prefix, userId, UUID.randomUUID().toString());
    }
}
