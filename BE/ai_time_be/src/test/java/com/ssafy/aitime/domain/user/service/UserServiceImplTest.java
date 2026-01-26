package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.dto.request.PasswordResetRequest;
import com.ssafy.aitime.domain.user.dto.request.UserJoinRequest;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.*;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.exception.InvalidPasswordException;
import com.ssafy.aitime.domain.user.exception.PhoneVerificationRequiredException;
import com.ssafy.aitime.domain.user.exception.UserAlreadyExistException;
import com.ssafy.aitime.domain.user.exception.UserNotFoundException;
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
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.AssertionsForClassTypes.assertThat;
import static org.assertj.core.api.AssertionsForClassTypes.assertThatThrownBy;
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
                .hasMessageContaining("비밀번호가 올바르지 않습니다.");
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

    @Test
    @DisplayName("휴대폰 번호로 아이디 조회 시 성공하면 아이디를 반환한다")
    void getIdByPhone_Success() {
        // given
        String phoneNumber = "01012345678";
        User user = User.builder()
                .loginId("findMe123")
                .phoneNumber(phoneNumber)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        // Redis 인증 완료 마크 설정
        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("AUTH_VERIFIED:" + phoneNumber)).thenReturn("true");

        when(userRepository.findByPhoneNumberAndRecordStatus(phoneNumber, RecordStatus.ACTIVE))
                .thenReturn(Optional.of(user));

        // when
        IdFindResponse response = userService.getIdByPhone(phoneNumber);

        // then
        assertThat(response.loginId()).isEqualTo("findMe123");
        verify(userRepository).findByPhoneNumberAndRecordStatus(phoneNumber, RecordStatus.ACTIVE);
    }

    @Test
    @DisplayName("본인 확인 요청 시 인증이 완료된 상태면 유저 UUID를 반환한다")
    void verifyUserIdentity_Success() {
        // given
        String phoneNumber = "01012345678";
        UUID userId = UUID.randomUUID();
        User user = mock(User.class);
        when(user.getUserId()).thenReturn(userId);

        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("AUTH_VERIFIED:" + phoneNumber)).thenReturn("true");

        when(userRepository.findByPhoneNumberAndRecordStatus(phoneNumber, RecordStatus.ACTIVE))
                .thenReturn(Optional.of(user));

        // when
        UserIdentityResponse response = userService.verifyUserIdentity(phoneNumber);

        // then
        assertThat(response.isVerified()).isTrue();
        assertThat(response.userId()).isEqualTo(userId);
    }

    @Test
    @DisplayName("비밀번호 재설정 시 유저를 찾지 못하면 UserNotFoundException이 발생한다")
    void resetPassword_Fail_UserNotFound() {
        // given
        PasswordResetRequest request = new PasswordResetRequest(UUID.randomUUID(), "newPw123!");
        when(userRepository.findByUserIdAndRecordStatus(any(), eq(RecordStatus.ACTIVE)))
                .thenReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> userService.resetPassword(request))
                .isInstanceOf(UserNotFoundException.class);
    }

    @Test
    @DisplayName("비밀번호 재설정 성공 시 비밀번호를 암호화하여 저장하고 Redis 마크를 삭제한다")
    void resetPassword_Success() {
// given
        UUID userId = UUID.randomUUID();
        String phoneNumber = "01012345678";
        PasswordResetRequest request = new PasswordResetRequest(userId, "newPw123!");

        // 1. 유저 객체 생성
        User user = User.builder()
                .phoneNumber(phoneNumber)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        // 2. [핵심] 리플렉션을 통해 private 필드인 userId에 강제로 값을 주입합니다.
        ReflectionTestUtils.setField(user, "userId", userId);

        // 3. 필드가 채워진 객체를 spy로 감쌉니다.
        User spyUser = spy(user);

        when(userRepository.findByUserIdAndRecordStatus(userId, RecordStatus.ACTIVE))
                .thenReturn(Optional.of(spyUser));

        // Redis 설정
        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("AUTH_VERIFIED:" + phoneNumber)).thenReturn("true");

        when(passwordEncoder.encode(request.password())).thenReturn("hashed-new-password");

        // when
        PasswordResetResponse response = userService.resetPassword(request);

        // then
        assertThat(response.userId()).isEqualTo(userId); // 이제 null이 아닌 UUID가 나옵니다!
        verify(spyUser).updatePassword("hashed-new-password");
        verify(redisTemplate).delete("AUTH_VERIFIED:" + phoneNumber);
    }

    @Test
    @DisplayName("인증 마크가 만료되거나 없을 경우 PhoneVerificationRequiredException이 발생한다")
    void validatePhoneVerification_Fail() {
        // given
        String phoneNumber = "01012345678";
        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("AUTH_VERIFIED:" + phoneNumber)).thenReturn(null); // 인증 마크 없음

        // when & then (getIdByPhone을 통해 private 메서드 검증)
        assertThatThrownBy(() -> userService.getIdByPhone(phoneNumber))
                .isInstanceOf(PhoneVerificationRequiredException.class);
    }
}