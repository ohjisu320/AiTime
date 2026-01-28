package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.request.HospitalStaffLoginRequest;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalStaffLoginResponse;
import com.ssafy.aitime.domain.hospital.dto.response.StaffTokenResponse;

public interface HospitalStaffService {
    StaffTokenResponse login(HospitalStaffLoginRequest request);
    StaffTokenResponse refresh(String refreshToken);
    void logout(String accessToken, String refreshToken);
}
