package com.ssafy.aitime.security.repository;

import com.ssafy.aitime.security.entity.RefreshToken;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.redis.test.autoconfigure.DataRedisTest;

import static org.assertj.core.api.AssertionsForClassTypes.assertThat;
import static org.junit.jupiter.api.Assertions.*;

@DataRedisTest
class RefreshTokenRepositoryTest {
    @Autowired
    private RefreshTokenRepository refreshTokenRepository;

    @Test
    @DisplayName("리프레시 토큰 저장 및 조회 테스트")
    void saveAndFindTest() {
        // given: 테스트 환경 준비
        RefreshToken token = RefreshToken.builder()
                .loginId("testUser01")
                .refreshToken("test-refresh-token")
                .expiration(600L) // 10분
                .build();

        // when: 실제 동작 수행
        refreshTokenRepository.save(token);
        RefreshToken savedToken = refreshTokenRepository.findById("testUser01").orElse(null);

        // then: 결과 검증
        assertThat(savedToken).isNotNull();
        assertThat(savedToken.getLoginId()).isEqualTo("testUser01");
        assertThat(savedToken.getRefreshToken()).isEqualTo("test-refresh-token");
    }
}