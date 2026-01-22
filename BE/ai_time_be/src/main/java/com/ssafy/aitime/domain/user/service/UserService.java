package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.UserLoginResponse;

public interface UserService {
    UserLoginResponse login(UserLoginRequest userLoginRequest);
}
