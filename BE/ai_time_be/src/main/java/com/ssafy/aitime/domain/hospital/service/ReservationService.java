package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.request.CalendarRequest;
import com.ssafy.aitime.domain.hospital.dto.response.CalendarReservationResponse;

import java.util.List;
import java.util.UUID;

public interface ReservationService {

    /**
     * 특정 의사의 년/월별 예약 날짜 조회
     * @param doctorId 의사 ID
     * @param calendarRequest year, month
     * @return CalendarReservationResponse
     */
    CalendarReservationResponse getReservationDates(UUID doctorId, CalendarRequest calendarRequest);

}
