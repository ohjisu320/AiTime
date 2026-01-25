package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.dto.request.UserJoinRequest;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.IdDuplicateResponse;
import com.ssafy.aitime.domain.user.dto.response.TokenResponse;
import com.ssafy.aitime.domain.user.dto.response.UserJoinResponse;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.exception.InvalidPasswordException;
import com.ssafy.aitime.domain.user.exception.PhoneVerificationRequiredException;
import com.ssafy.aitime.domain.user.exception.UserAlreadyExistException;
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
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;

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
    private PasswordEncoder passwordEncoder;
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

    @Test
    @DisplayName("아이디가 중복되지 않으면 중복 여부 false를 반환한다")
    void checkIdDuplicate_False() {
        // given
        String loginId = "newId";
        when(userRepository.existsByLoginId(loginId)).thenReturn(false);

        // when
        IdDuplicateResponse response = userService.checkIdDuplicate(loginId);

        // then
        assertThat(response.isDuplicate()).isFalse();
        verify(userRepository, times(1)).existsByLoginId(loginId);
    }

    @Test
    @DisplayName("이미 존재하는 아이디로 가입 시 UserAlreadyExistException이 발생한다")
    void join_Fail_DuplicateId() {
        // given
        UserJoinRequest request = new UserJoinRequest("dupId", "pw", "name", "01012345678", true);

        // 휴대폰 인증은 통과했다고 가정 (Redis Mock 설정)
        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("AUTH_VERIFIED:" + request.phoneNumber())).thenReturn("true");

        // 아이디가 이미 존재한다고 가정
        when(userRepository.existsByLoginId(request.loginId())).thenReturn(true);

        // when & then
        assertThatThrownBy(() -> userService.join(request))
                .isInstanceOf(UserAlreadyExistException.class);
    }

    @Test
    @DisplayName("휴대폰 인증이 되지 않은 번호로 가입 시 PhoneVerificationRequiredException이 발생한다")
    void join_Fail_UnverifiedPhone() {
        // given
        UserJoinRequest request = new UserJoinRequest("id", "pw", "name", "01012345678", true);

        // Redis에 인증 정보가 없다고 가정
        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("AUTH_VERIFIED:" + request.phoneNumber())).thenReturn(null);

        // when & then
        // 주의: 현재 UserServiceImpl에서 이 로직이 주석처리 되어 있다면 이 테스트는 실패할 수 있습니다.
        // 로직을 활성화한 후 테스트하시거나, 주석 처리된 상태라면 이 테스트도 잠시 제외해주세요.
        assertThatThrownBy(() -> userService.join(request))
                .isInstanceOf(PhoneVerificationRequiredException.class);
    }

    @Test
    @DisplayName("회원가입 성공 시 저장된 유저 정보를 반환한다")
    void join_Success() {
        // given
        UserJoinRequest request = new UserJoinRequest("parent1", "password!", "홍길동", "01012345678", true);

        // 1. Redis 인증 확인 Mock
        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("AUTH_VERIFIED:" + request.phoneNumber())).thenReturn("true");

        // 2. 아이디 중복 체크 Mock
        when(userRepository.existsByLoginId(request.loginId())).thenReturn(false);

        // 3. 비밀번호 암호화 Mock
        when(passwordEncoder.encode(request.password())).thenReturn("encrypted-password");

        // 4. 리포지토리 저장 Mock
        UUID generatedId = UUID.randomUUID();
        User user = User.builder()
                .loginId(request.loginId())
                .name(request.name())
                .build();
        // ID 필드에 값을 주입하기 위해 리플렉션이나 가짜 엔티티 사용
        User savedUser = mock(User.class);
        when(savedUser.getUserId()).thenReturn(generatedId);
        when(savedUser.getLoginId()).thenReturn(request.loginId());
        when(savedUser.getName()).thenReturn(request.name());

        when(userRepository.save(any(User.class))).thenReturn(savedUser);

        // when
        UserJoinResponse response = userService.join(request);

        // then
        assertThat(response.userId()).isEqualTo(generatedId);
        assertThat(response.loginId()).isEqualTo(request.loginId());
        verify(userRepository, times(1)).save(any(User.class));
    }
}