package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.IdDuplicateResponse;
import com.ssafy.aitime.domain.user.dto.response.TokenResponse;

public interface UserService {
    TokenResponse login(UserLoginRequest userLoginRequest);
    TokenResponse refresh(String refreshToken);
    void logout(String accessToken, String refreshToken);
    IdDuplicateResponse checkIdDuplicate(String loginId);
}
