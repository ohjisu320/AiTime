package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.domain.user.dto.request.UserJoinRequest;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.IdDuplicateResponse;
import com.ssafy.aitime.domain.user.dto.response.IdFindResponse;
import com.ssafy.aitime.domain.user.dto.response.TokenResponse;
import com.ssafy.aitime.domain.user.dto.response.UserJoinResponse;

public interface UserService {
    TokenResponse login(UserLoginRequest userLoginRequest);
    TokenResponse refresh(String refreshToken);
    void logout(String accessToken, String refreshToken);
    IdDuplicateResponse checkIdDuplicate(String loginId);
    UserJoinResponse join(UserJoinRequest request);
    IdFindResponse getIdByPhone(String phoneNumber);
}
