package com.ssafy.aitime.domain.screening.service;

import com.ssafy.aitime.domain.screening.dto.request.ScreeningCompleteRequest;
import com.ssafy.aitime.domain.screening.dto.request.StartScreeningRequest;
import com.ssafy.aitime.domain.screening.dto.response.ScreeningSessionResponse;
import com.ssafy.aitime.domain.screening.dto.response.ScreeningStatusResponse;

import java.util.UUID;

public interface ScreeningService {
    /**
     * 스크리닝 세션 시작
     */
    ScreeningSessionResponse startScreening(UUID userId, StartScreeningRequest request);

    /**
     * AI 서버로부터 스크리닝 완료 알림 수신
     */
    void completeScreening(ScreeningCompleteRequest request);

    /**
     * 세션 상태 조회
     */
    ScreeningStatusResponse getSessionStatus(UUID sessionId);

    /**
     * 사용자 세션 조회 (userId로)
     */
    ScreeningStatusResponse getUserSession(UUID userId);
}
