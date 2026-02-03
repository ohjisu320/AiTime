package com.ssafy.aitime.domain.screening.service;

import com.ssafy.aitime.domain.screening.dto.request.ScreeningCompleteRequest;
import com.ssafy.aitime.domain.screening.dto.request.StartScreeningRequest;
import com.ssafy.aitime.domain.screening.dto.response.ScreeningSessionResponse;
import com.ssafy.aitime.domain.screening.dto.response.ScreeningStatusResponse;
import com.ssafy.aitime.domain.screening.entity.enums.ScreeningStatus;
import com.ssafy.aitime.domain.screening.exception.ActiveScreeningException;
import com.ssafy.aitime.domain.screening.exception.LiveKitException;
import com.ssafy.aitime.domain.screening.exception.ScreeningNotFoundException;
import com.ssafy.aitime.domain.screening.repository.ScreeningSessionRedisRepository;
import com.ssafy.aitime.domain.screening.service.dto.ScreeningSessionDTO;
import com.ssafy.aitime.infra.livekit.service.AiServerService;
import com.ssafy.aitime.infra.livekit.service.LiveKitService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class ScreeningServiceImpl implements ScreeningService {

    private final ScreeningSessionRedisRepository sessionRepository;
    private final LiveKitService liveKitService;
    private final AiServerService aiServerService;

    @Override
    public ScreeningSessionResponse startScreening(UUID userId, StartScreeningRequest request) {
        // 1. 이미 진행 중인 세션이 있는지 확인
        sessionRepository.findByUserId(userId).ifPresent(session -> {
            if (session.status() == ScreeningStatus.IN_PROGRESS ||
                    session.status() == ScreeningStatus.PENDING) {
                throw new ActiveScreeningException();
            }
        });

        // 2. Room 이름 생성 및 LiveKit Room 생성
        UUID sessionId = UUID.randomUUID();
        String roomName = liveKitService.generateRoomName(userId.getMostSignificantBits(), "screening");

        try {
            liveKitService.createRoom(roomName);
        } catch (Exception e) {
            log.error("Failed to create LiveKit room", e);
            throw new LiveKitException("LiveKit 방 생성에 실패했습니다.", e);
        }

        // 3. 사용자용 토큰 생성
        String userParticipantName = "user-" + userId.toString();
        String userToken = liveKitService.generateUserToken(roomName, userParticipantName);

        // 4. AI용 토큰 생성
        String aiParticipantName = "ai-agent-" + sessionId.toString();
        String aiToken = liveKitService.generateAiToken(roomName, aiParticipantName);

        // 5. 세션 DTO 생성 및 Redis 저장
        ScreeningSessionDTO session = new ScreeningSessionDTO(
                sessionId,
                roomName,
                userId,
                ScreeningStatus.PENDING,
                null,
                null,
                null,
                null,
                LocalDateTime.now()
        );
        sessionRepository.save(session);

        // 6. AI 서버에 분석 시작 요청 (비동기)
        // 6. AI 서버에 분석 시작 요청 (비동기)
        aiServerService.startAnalysis(roomName, aiToken, sessionId.getMostSignificantBits())
                .doOnError(error -> {
                    // AI 서버 호출 실패 시 세션 삭제
                    log.error("AI server call failed, cleaning up session: {}", sessionId, error);
                    sessionRepository.deleteWithUserMapping(roomName, userId);
                })
                .onErrorResume(e -> {
                    // 에러 발생해도 계속 진행 (세션 삭제 후 빈 Mono 반환)
                    log.warn("AI server call failed, session cleaned up");
                    return Mono.empty();
                })
                .subscribe();  //

        log.info("Started screening session: {} for user: {}", sessionId, userId);

        return new ScreeningSessionResponse(
                sessionId,
                roomName,
                userToken,
                ScreeningStatus.PENDING,
                LocalDateTime.now()
        );
    }

    @Override
    public void completeScreening(ScreeningCompleteRequest request) {
        ScreeningSessionDTO session = sessionRepository.findByRoomName(request.roomName())
                .orElseThrow(ScreeningNotFoundException::new);

        ScreeningStatus newStatus = "success".equals(request.status())
                ? ScreeningStatus.READY
                : ScreeningStatus.FAILED;

        ScreeningSessionDTO updatedSession = new ScreeningSessionDTO(
                session.sessionId(),
                session.roomName(),
                session.userId(),
                newStatus,
                session.userParticipantId(),
                session.aiParticipantId(),
                session.startedAt(),
                LocalDateTime.now(),
                session.createdAt()
        );

        sessionRepository.save(updatedSession);

        log.info("Screening {} for session: {}",
                newStatus == ScreeningStatus.READY ? "completed" : "failed",
                session.sessionId());
    }

    @Override
    public ScreeningStatusResponse getSessionStatus(UUID sessionId) {
        // Redis는 sessionId로 직접 조회가 안 되므로, 실제로는 roomName이나 userId로 조회해야 함
        // 여기서는 예외 처리만 해둠
        throw new UnsupportedOperationException("sessionId로 조회는 지원하지 않습니다. roomName이나 userId를 사용하세요.");
    }

    @Override
    public ScreeningStatusResponse getUserSession(UUID userId) {
        ScreeningSessionDTO session = sessionRepository.findByUserId(userId)
                .orElseThrow(ScreeningNotFoundException::new);

        String message = switch (session.status()) {
            case PENDING -> "AI 연결 대기 중입니다.";
            case IN_PROGRESS -> "스크리닝이 진행 중입니다.";
            case READY -> "스크리닝이 완료되었습니다. 녹화를 시작할 수 있습니다.";
            case FAILED -> "스크리닝에 실패했습니다.";
            case TIMEOUT -> "스크리닝 시간이 초과되었습니다.";
        };

        return new ScreeningStatusResponse(
                session.sessionId(),
                session.roomName(),
                session.status(),
                message
        );
    }
}
