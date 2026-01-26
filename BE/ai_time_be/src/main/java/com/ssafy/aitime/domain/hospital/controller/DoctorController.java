package com.ssafy.aitime.domain.hospital.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;
import com.ssafy.aitime.domain.hospital.service.DoctorService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/doctor/")
@RequiredArgsConstructor
public class DoctorController {

    private final DoctorService doctorService;

    /**
     * 환자 목록 조회 (검색 및 필터링)
     * TODO: 인증 구현 후 @AuthenticationPrincipal 사용으로 변경
     */
    @GetMapping("/patients")
    public ResponseEntity<ApiResponse<PatientSearchResponse>> getSearchPatientList(
            //@AuthenticationPrincipal UserPrincipal user
            // 임시 : 헤더로 doctorId 전달 (개발/테스트용)
            @RequestHeader(value = "X-DOCTOR-ID", defaultValue = "550e8400-e29b-41d4-a716-446655440000")
            UUID doctorId,
            @ModelAttribute @Valid PatientSearchRequest patientSearchRequest
    ) {
        return ResponseEntity.ok(
                //ApiResponse.ok(doctorService.getSearchPatientList(user.getUserId()))
                ApiResponse.ok(doctorService.getSearchPatientList(doctorId, patientSearchRequest))
        );
    }

}
