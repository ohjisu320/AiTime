package com.ssafy.aitime.domain.screening.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.screening.dto.request.ScreeningCompleteRequest;
import com.ssafy.aitime.domain.screening.dto.request.StartScreeningRequest;
import com.ssafy.aitime.domain.screening.dto.response.ScreeningSessionResponse;
import com.ssafy.aitime.domain.screening.dto.response.ScreeningStatusResponse;
import com.ssafy.aitime.domain.screening.service.ScreeningService;
import com.ssafy.aitime.security.principal.UserPrincipal;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/screening")
@RequiredArgsConstructor
public class ScreeningController {

    private final ScreeningService screeningService;

    /**
     * 스크리닝 세션 시작
     * 프론트엔드가 이 API를 호출하여 LiveKit 토큰을 받아갑니다.
     */
    @PostMapping("/start")
    public ResponseEntity<ApiResponse<ScreeningSessionResponse>> startScreening(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Valid @RequestBody StartScreeningRequest request) {

        log.info("Starting screening for user: {}, child: {}",
                userPrincipal.getUserId(), request.childId());

        ScreeningSessionResponse response = screeningService.startScreening(
                userPrincipal.getUserId(), request);

        return ResponseEntity.ok(
                ApiResponse.ok("스크리닝 세션이 시작되었습니다.", response)
        );
    }

    /**
     * AI 서버로부터 스크리닝 완료 알림 수신
     * FastAPI가 스크리닝 완료 후 이 API를 호출합니다.
     */
    @PostMapping("/complete")
    public ResponseEntity<ApiResponse<Void>> completeScreening(
            @Valid @RequestBody ScreeningCompleteRequest request) {

        log.info("Received screening complete for room: {}, status: {}",
                request.roomName(), request.status());

        screeningService.completeScreening(request);

        return ResponseEntity.ok(
                ApiResponse.ok("스크리닝 완료 처리되었습니다.", null)
        );
    }

    /**
     * 현재 사용자의 스크리닝 상태 조회
     */
    @GetMapping("/status")
    public ResponseEntity<ApiResponse<ScreeningStatusResponse>> getMyScreeningStatus(
            @AuthenticationPrincipal UserPrincipal userPrincipal) {

        ScreeningStatusResponse response = screeningService.getUserSession(
                userPrincipal.getUserId());

        return ResponseEntity.ok(
                ApiResponse.ok("스크리닝 상태 조회가 완료되었습니다.", response)
        );
    }
}
