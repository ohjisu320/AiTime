package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.TokenResponse;
import com.ssafy.aitime.domain.user.dto.response.UserLoginResponse;

public interface UserService {
    TokenResponse login(UserLoginRequest userLoginRequest);
}
