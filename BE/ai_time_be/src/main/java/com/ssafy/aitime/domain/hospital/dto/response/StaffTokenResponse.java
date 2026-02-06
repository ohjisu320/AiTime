package com.ssafy.aitime.domain.hospital.dto.response;

import com.ssafy.aitime.domain.hospital.service.dto.HospitalStaffInfoDTO;

public record StaffTokenResponse(
        String accessToken,
        String refreshToken,
        HospitalStaffInfoDTO staffInfo
) {
}
