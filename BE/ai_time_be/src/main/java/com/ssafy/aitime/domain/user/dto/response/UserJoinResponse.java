package com.ssafy.aitime.domain.user.dto.response;


import com.ssafy.aitime.domain.user.service.dto.UserInfoDTO;

import java.util.UUID;

public record UserJoinResponse(
        UUID userId,
        String loginId,
        String name
){
}
