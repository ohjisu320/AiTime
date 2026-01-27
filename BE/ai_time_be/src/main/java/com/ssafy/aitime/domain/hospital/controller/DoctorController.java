package com.ssafy.aitime.domain.hospital.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.hospital.dto.request.CalendarRequest;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.CalendarReservationResponse;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;
import com.ssafy.aitime.domain.hospital.service.DoctorService;
import com.ssafy.aitime.domain.hospital.service.ReservationService;
import com.ssafy.aitime.security.principal.UserPrincipal;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;


@RestController
@RequestMapping("/doctor/")
@RequiredArgsConstructor
public class DoctorController {

    private final DoctorService doctorService;
    private final ReservationService reservationService;

    /**
     * 환자 목록 조회 (검색 및 필터링)
     * TODO: 인증 구현 후 @AuthenticationPrincipal 사용으로 변경
     */
    @GetMapping("/patients")
    public ResponseEntity<ApiResponse<PatientSearchResponse>> getSearchPatientList(
            @AuthenticationPrincipal UserPrincipal user,
            UUID doctorId,
            @ModelAttribute @Valid PatientSearchRequest patientSearchRequest
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok(doctorService.getSearchPatientList(user.getUserId(), patientSearchRequest))
        );
    }

    /**
     * 의사별 월별 예약 여부 조회 (캘린더)
     * GET /api/v1/doctor/reservations/calendar?year=2026&month=01
     */
    @Operation(
            summary = "의사별 월별 예약 캘린더 조회",
            description = "특정 년/월에 해당 의사에게 배정된 예약이 있는 날짜 목록을 반환합니다."
    )
    @ApiResponses({
            @io.swagger.v3.oas.annotations.responses.ApiResponse(
                    responseCode = "200",
                    description = "조회 성공"
            ),
            @io.swagger.v3.oas.annotations.responses.ApiResponse(
                    responseCode = "400",
                    description = "잘못된 파라미터"
            ),
            @io.swagger.v3.oas.annotations.responses.ApiResponse(
                    responseCode = "401",
                    description = "인증 실패"
            )
    })
    @GetMapping("/reservations/calendar")
    public ResponseEntity<ApiResponse<CalendarReservationResponse>> getReservationCalendar(
            @AuthenticationPrincipal UserPrincipal user,
            @ModelAttribute @Valid CalendarRequest calendarRequest) {

        return ResponseEntity.ok(
                ApiResponse.ok("예약 날짜 조회 완료", reservationService.getReservationDates(user.getUserId(), calendarRequest))
        );
    }

}
