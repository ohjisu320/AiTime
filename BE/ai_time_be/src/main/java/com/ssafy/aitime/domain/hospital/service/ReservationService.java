package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.request.CalendarRequest;
import com.ssafy.aitime.domain.hospital.dto.request.ReservationCreateRequest;
import com.ssafy.aitime.domain.hospital.dto.response.CalendarReservationResponse;
import com.ssafy.aitime.domain.hospital.dto.response.ReservationListResponse;

import java.time.LocalDate;
import java.time.YearMonth;
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

    void insertReservation(ReservationCreateRequest reservationCreateRequest);
    /*
        해당 병원의 년/월별 예약 날짜 조회
     */
    List<LocalDate> getHospitalReservationDates(UUID hospitalId, int year, int month);

    List<ReservationListResponse> getReservationList(UUID hospitalId, LocalDate date);
}
