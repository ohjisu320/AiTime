package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.domain.user.dto.request.PasswordResetRequest;
import com.ssafy.aitime.domain.user.dto.request.UserJoinRequest;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.request.UserUpdateRequest;
import com.ssafy.aitime.domain.user.dto.response.*;

import java.util.UUID;

public interface UserService {
    TokenResponse login(UserLoginRequest userLoginRequest);
    TokenResponse refresh(String refreshToken);
    void logout(String accessToken, String refreshToken);
    IdDuplicateResponse checkIdDuplicate(String loginId);
    UserJoinResponse join(UserJoinRequest request);
    IdFindResponse getIdByPhone(String phoneNumber);
    UserIdentityResponse verifyUserIdentity(String phoneNumber);
    PasswordResetResponse resetPassword(PasswordResetRequest request);
    UserMeResponse getUserInfo(UUID userId);
    UserUpdateResponse updateUserInfo(UUID userId, UserUpdateRequest request);
    void withdraw(UUID userId, String accessToken, String refreshToken);
}
