package com.ssafy.aitime.domain.screening.controller;

import com.ssafy.aitime.domain.screening.entity.enums.ScreeningStatus;
import com.ssafy.aitime.domain.screening.repository.ScreeningSessionRedisRepository;
import com.ssafy.aitime.domain.screening.service.dto.ScreeningSessionDTO;
import io.livekit.server.WebhookReceiver;
import livekit.LivekitWebhook;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@Slf4j
@RestController
@RequestMapping("/livekit")
@RequiredArgsConstructor
public class LiveKitWebhookController {
    private final ScreeningSessionRedisRepository sessionRepository;

    @Value("${livekit.api-key}")
    private String apiKey;

    @Value("${livekit.api-secret}")
    private String apiSecret;

    /**
     * LiveKit Webhook 이벤트 수신
     * LiveKit 서버 설정에서 이 엔드포인트를 Webhook URL로 등록해야 합니다.
     */
    @PostMapping("/webhook")
    public ResponseEntity<Void> handleWebhook(
            @RequestBody String body,
            @RequestHeader("Authorization") String authHeader) {

        try {
            WebhookReceiver receiver = new WebhookReceiver(apiKey, apiSecret);
            LivekitWebhook.WebhookEvent event = receiver.receive(body, authHeader);

            log.info("Received LiveKit webhook event: {}", event.getEvent());

            switch (event.getEvent()) {
                case "participant_joined":
                    handleParticipantJoined(event);
                    break;

                case "participant_left":
                    handleParticipantLeft(event);
                    break;

                case "room_finished":
                    handleRoomFinished(event);
                    break;

                default:
                    log.debug("Unhandled event type: {}", event.getEvent());
            }

            return ResponseEntity.ok().build();

        } catch (Exception e) {
            log.error("Failed to process webhook", e);
            return ResponseEntity.badRequest().build();
        }
    }

    private void handleParticipantJoined(LivekitWebhook.WebhookEvent event) {
        String roomName = event.getRoom().getName();
        String participantId = event.getParticipant().getIdentity();

        log.info("Participant joined - Room: {}, Participant: {}", roomName, participantId);

        sessionRepository.findByRoomName(roomName).ifPresent(session -> {
            ScreeningSessionDTO updatedSession;

            if (participantId.startsWith("user-")) {
                // 사용자 입장 → 스크리닝 시작
                updatedSession = new ScreeningSessionDTO(
                        session.sessionId(),
                        session.roomName(),
                        session.userId(),
                        ScreeningStatus.IN_PROGRESS,
                        participantId,
                        session.aiParticipantId(),
                        LocalDateTime.now(),
                        session.completedAt(),
                        session.createdAt()
                );
            } else if (participantId.startsWith("ai-agent-")) {
                // AI 입장
                updatedSession = new ScreeningSessionDTO(
                        session.sessionId(),
                        session.roomName(),
                        session.userId(),
                        session.status(),
                        session.userParticipantId(),
                        participantId,
                        session.startedAt(),
                        session.completedAt(),
                        session.createdAt()
                );
            } else {
                return;
            }

            sessionRepository.save(updatedSession);
        });
    }

    private void handleParticipantLeft(LivekitWebhook.WebhookEvent event) {
        String roomName = event.getRoom().getName();
        String participantId = event.getParticipant().getIdentity();

        log.info("Participant left - Room: {}, Participant: {}", roomName, participantId);

        // 사용자가 중도 이탈하면 세션 실패 처리
        if (participantId.startsWith("user-")) {
            sessionRepository.findByRoomName(roomName).ifPresent(session -> {
                if (session.status() == ScreeningStatus.IN_PROGRESS) {
                    ScreeningSessionDTO failedSession = new ScreeningSessionDTO(
                            session.sessionId(),
                            session.roomName(),
                            session.userId(),
                            ScreeningStatus.FAILED,
                            session.userParticipantId(),
                            session.aiParticipantId(),
                            session.startedAt(),
                            LocalDateTime.now(),
                            session.createdAt()
                    );
                    sessionRepository.save(failedSession);
                }
            });
        }
    }

    private void handleRoomFinished(LivekitWebhook.WebhookEvent event) {
        String roomName = event.getRoom().getName();
        log.info("Room finished: {}", roomName);

        // Room 종료되면 Redis에서 세션 삭제
        sessionRepository.findByRoomName(roomName).ifPresent(session -> {
            sessionRepository.deleteWithUserMapping(roomName, session.userId());
        });
    }
}
