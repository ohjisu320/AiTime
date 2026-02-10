package com.ssafy.aitime.domain.hospital.dto.request;

import jakarta.validation.constraints.NotBlank;

public record HospitalStaffLoginRequest(
        @NotBlank String loginId,
        @NotBlank String password
) {
}
