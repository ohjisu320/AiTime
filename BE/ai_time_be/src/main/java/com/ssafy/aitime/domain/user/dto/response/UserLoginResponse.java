package com.ssafy.aitime.domain.user.dto.response;


import com.ssafy.aitime.domain.user.service.dto.UserInfoDTO;

public record UserLoginResponse (
        String accessToken,
        UserInfoDTO userInfoDTO
){
}
