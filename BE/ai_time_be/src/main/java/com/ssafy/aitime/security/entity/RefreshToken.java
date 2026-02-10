package com.ssafy.aitime.security.entity;

import lombok.Builder;
import lombok.Getter;
import org.springframework.data.annotation.Id;
import org.springframework.data.redis.core.RedisHash;
import org.springframework.data.redis.core.TimeToLive;

@Getter
@Builder
@RedisHash(value = "refreshToken")
public class RefreshToken {
    @Id
    private String loginId; // 사용자 로그인 ID를 Key로 사용

    private String refreshToken;

    @TimeToLive // application.yml에 설정한 만료 시간과 동기화
    private Long expiration;
}
