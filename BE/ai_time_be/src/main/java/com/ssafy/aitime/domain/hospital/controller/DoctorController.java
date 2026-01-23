package com.ssafy.aitime.domain.hospital.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.hospital.dto.response.TotalPatientListResponse;
import com.ssafy.aitime.domain.hospital.service.DoctorService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/doctors/me")
@RequiredArgsConstructor
public class DoctorController {

    private final DoctorService doctorService;

    @GetMapping("/patients")
    public ResponseEntity<ApiResponse<TotalPatientListResponse>> totalPatientList(
            //@AuthenticationPrincipal UserPrincipal user
            @RequestHeader(value = "X-DOCTOR-ID", defaultValue = "550e8400-e29b-41d4-a716-446655440000")
            UUID doctorId
    ) {
        return ResponseEntity.ok(
                //ApiResponse.ok(doctorService.getTotalPatientList(user.getUserId()))
                ApiResponse.ok(doctorService.getTotalPatientList(doctorId))
        );
    }

}
