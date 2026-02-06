package com.ssafy.aitime.domain.hospital.dto.response;

import jakarta.validation.constraints.NotNull;
import lombok.Builder;

import java.util.List;

/**
 * 의사별 월별 예약 캘린더 응답 DTO
 */
@Builder
public record CalendarReservationResponse(
        @NotNull(message = "데이터는 필수입니다")
        List<String> data
) {
        /**
         * 정적 팩토리 메서드
         */
        public static CalendarReservationResponse of(List<String> dates) {
                return new CalendarReservationResponse(dates);
        }
}
