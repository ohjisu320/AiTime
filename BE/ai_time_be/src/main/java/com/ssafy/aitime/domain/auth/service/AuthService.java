package com.ssafy.aitime.domain.auth.service;

import com.ssafy.aitime.domain.auth.dto.response.PhoneVerificationResponse;

public interface AuthService {
    PhoneVerificationResponse sendVerificationCode(String phoneNumber);
}
