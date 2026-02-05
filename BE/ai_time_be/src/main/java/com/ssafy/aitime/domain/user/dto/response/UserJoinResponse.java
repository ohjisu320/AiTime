package com.ssafy.aitime.domain.user.dto.response;


import java.util.UUID;

public record UserJoinResponse(
        UUID userId,
        String loginId,
        String name
){
}
