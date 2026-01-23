package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.TokenResponse;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.exception.InvalidPasswordException;
import com.ssafy.aitime.domain.user.repository.UserRepository;
import com.ssafy.aitime.security.entity.RefreshToken;
import com.ssafy.aitime.security.principal.UserPrincipal;
import com.ssafy.aitime.security.provider.JwtTokenProvider;
import com.ssafy.aitime.security.repository.RefreshTokenRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;

import java.util.UUID;

import static org.assertj.core.api.AssertionsForClassTypes.assertThat;
import static org.assertj.core.api.AssertionsForClassTypes.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {

    @InjectMocks
    private UserServiceImpl userService; // 테스트 대상




    @Mock
    private AuthenticationManager authenticationManager;
    @Mock
    private JwtTokenProvider jwtTokenProvider;
    @Mock
    private StringRedisTemplate redisTemplate;
    @Mock
    private RefreshTokenRepository refreshTokenRepository;
    @Mock
    private UserRepository userRepository;

    @Test
    @DisplayName("로그인 성공 시 토큰을 반환하고 Redis에 저장한다")
    void loginSuccess() {
        // given
        User user = User.builder()
                .loginId("testUser")
                .password("encodedPassword")
                .name("홍길동")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        UserPrincipal principal = UserPrincipal.from(user);
        UserLoginRequest request = new UserLoginRequest("testUser", "password123");
        Authentication auth = mock(Authentication.class);

        when(authenticationManager.authenticate(any())).thenReturn(auth);
        when(auth.getPrincipal()).thenReturn(principal);
        when(jwtTokenProvider.createAccessToken(anyString(), anyString())).thenReturn("access-token");
        when(jwtTokenProvider.createRefreshToken(anyString())).thenReturn("refresh-token");

        // when
        TokenResponse response = userService.login(request);

        // then
        assertThat(response.accessToken()).isEqualTo("access-token");
        assertThat(response.refreshToken()).isEqualTo("refresh-token");
        verify(refreshTokenRepository, times(1)).save(any(RefreshToken.class)); // 저장 메서드 호출 확인
    }

    @Test
    @DisplayName("비밀번호 불일치 시 InvalidPasswordException이 발생한다")
    void loginFailByPassword() {
        // given
        when(authenticationManager.authenticate(any())).thenThrow(new BadCredentialsException("wrong password"));

        // when & then
        assertThatThrownBy(() -> userService.login(new UserLoginRequest("id", "wrong")))
                .isInstanceOf(InvalidPasswordException.class)
                .hasMessageContaining("아이디 또는 비밀번호가 일치하지 않습니다.");
    }
}