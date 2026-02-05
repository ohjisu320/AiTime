package com.ssafy.aitime.domain.hospital.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamWithVideosResponse;
import com.ssafy.aitime.domain.hospital.dto.request.CalendarRequest;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.AdosReportGraphsResponse;
import com.ssafy.aitime.domain.hospital.dto.response.CalendarReservationResponse;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;
import com.ssafy.aitime.domain.hospital.service.DoctorService;
import com.ssafy.aitime.domain.hospital.service.ReservationService;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
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
            @AuthenticationPrincipal HospitalStaffPrincipal principal,
            @ModelAttribute @Valid PatientSearchRequest patientSearchRequest
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok(doctorService.getSearchPatientList(principal.getHospitalStaffId(), patientSearchRequest))
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
            @AuthenticationPrincipal HospitalStaffPrincipal principal,
            @ModelAttribute @Valid CalendarRequest calendarRequest) {

        return ResponseEntity.ok(
                ApiResponse.ok("예약 날짜 조회 완료", reservationService.getReservationDates(principal.getHospitalStaffId(), calendarRequest))
        );
    }

    @Operation(
            summary = "환아별 검사 목록 조회",
            description = "특정 환아의 검사 목록을 최신순으로 조회하고, 각 검사에 속한 비디오 목록을 함께 반환합니다."
    )
    @ApiResponses({
            @io.swagger.v3.oas.annotations.responses.ApiResponse(
                    responseCode = "200",
                    description = "조회 성공"
            ),
            @io.swagger.v3.oas.annotations.responses.ApiResponse(
                    responseCode = "401",
                    description = "인증 실패"
            ),
            @io.swagger.v3.oas.annotations.responses.ApiResponse(
                    responseCode = "403",
                    description = "권한 없음 (다른 병원의 환아)"
            ),
            @io.swagger.v3.oas.annotations.responses.ApiResponse(
                    responseCode = "404",
                    description = "환아를 찾을 수 없음"
            )
    })
    @GetMapping("/{hospitalChildrenId}/exams")
    public ResponseEntity<ApiResponse<List<ExamWithVideosResponse>>> getExamsByHospitalChildren(
            @AuthenticationPrincipal HospitalStaffPrincipal principal,
            @PathVariable("hospitalChildrenId") UUID hospitalChildrenId) {

        List<ExamWithVideosResponse> response = doctorService.getExamsByHospitalChildren(
                principal.getHospitalStaffId(),
                hospitalChildrenId
        );

        return ResponseEntity.ok(
                ApiResponse.ok("환아별 검사 목록 조회 완료", response)
        );
    }

    @Operation(
            summary = "환아 ADOS 시계열 그래프 조회",
            description = "특정 환아의 검사 히스토리를 바탕으로 4개 영역의 ADOS 점수 추이 데이터를 반환합니다."
    )
    @GetMapping("/{hospitalChildrenId}/exam-reports/ados-graphs")
    public ResponseEntity<ApiResponse<AdosReportGraphsResponse>> getAdosGraphs(
            @AuthenticationPrincipal HospitalStaffPrincipal principal,
            @PathVariable("hospitalChildrenId") UUID hospitalChildrenId) {

        AdosReportGraphsResponse response = doctorService.getAdosGraphData(
                principal.getHospitalStaffId(),
                hospitalChildrenId
        );

        return ResponseEntity.ok(ApiResponse.ok("ADOS 그래프 데이터 조회 완료", response));
    }
}
