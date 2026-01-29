package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.hospital.dto.request.HospitalStaffLoginRequest;
import com.ssafy.aitime.domain.hospital.dto.response.StaffTokenResponse;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.repository.HospitalStaffRepository;
import com.ssafy.aitime.security.entity.RefreshToken;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
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
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

import static java.nio.file.Paths.get;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@ExtendWith(MockitoExtension.class)
class HospitalStaffServiceImplTest {

    @InjectMocks
    private HospitalStaffServiceImpl hospitalStaffService;

    @Mock
    private AuthenticationManager staffAuthenticationManager;

    @Mock
    private JwtTokenProvider jwtTokenProvider;

    @Mock
    private RefreshTokenRepository refreshTokenRepository;

    @Mock
    private HospitalStaffRepository hospitalStaffRepository;

    @Mock
    private StringRedisTemplate redisTemplate;

    @Test
    @DisplayName("병원 직원 로그인 성공 시 토큰을 반환하고 Redis에 저장한다")
    void loginSuccess() {
        // given
        UUID hospitalId = UUID.randomUUID();
        UUID staffId = UUID.randomUUID();

        Hospital hospital = mock(Hospital.class);
        when(hospital.getHospitalId()).thenReturn(hospitalId);

        HospitalStaff staff = HospitalStaff.builder()
                .hospital(hospital)
                .loginId("doctor01")
                .password("encodedPassword")
                .name("김의사")
                .staffRole(StaffRole.DOCTOR)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        ReflectionTestUtils.setField(staff, "hospitalStaffId", staffId);

        HospitalStaffPrincipal principal = HospitalStaffPrincipal.from(staff);
        HospitalStaffLoginRequest request = new HospitalStaffLoginRequest("doctor01", "password123");
        Authentication auth = mock(Authentication.class);

        when(staffAuthenticationManager.authenticate(any())).thenReturn(auth);
        when(auth.getPrincipal()).thenReturn(principal);
        when(jwtTokenProvider.createAccessToken(anyString(), anyString(), eq("STAFF")))
                .thenReturn("staff-access-token");
        when(jwtTokenProvider.createRefreshToken(anyString(), eq("STAFF")))
                .thenReturn("staff-refresh-token");

        // when
        StaffTokenResponse response = hospitalStaffService.login(request);

        // then
        assertThat(response.accessToken()).isEqualTo("staff-access-token");
        assertThat(response.refreshToken()).isEqualTo("staff-refresh-token");
        assertThat(response.staffInfo().hospitalStaffId()).isEqualTo(staffId);
        assertThat(response.staffInfo().name()).isEqualTo("김의사");
        assertThat(response.staffInfo().staffRole()).isEqualTo(StaffRole.DOCTOR);
        verify(refreshTokenRepository, times(1)).save(any(RefreshToken.class));
    }

    @Test
    @DisplayName("비밀번호 불일치 시 IllegalArgumentException이 발생한다")
    void loginFailByPassword() {
        // given
        when(staffAuthenticationManager.authenticate(any()))
                .thenThrow(new BadCredentialsException("wrong password"));

        // when & then
        assertThatThrownBy(() -> hospitalStaffService.login(
                new HospitalStaffLoginRequest("doctor01", "wrongPassword")))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("아이디 또는 비밀번호가 틀렸습니다.");
    }

    @Test
    @DisplayName("리프레시 토큰 검증 실패 시 IllegalArgumentException이 발생한다")
    void refreshFailByInvalidToken() {
        // given
        String invalidToken = "invalid-refresh-token";
        when(jwtTokenProvider.validateToken(invalidToken)).thenReturn(false);

        // when & then
        assertThatThrownBy(() -> hospitalStaffService.refresh(invalidToken))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("유효하지 않은 토큰입니다.");
    }

    @Test
    @DisplayName("Redis에 저장된 토큰과 불일치 시 IllegalArgumentException이 발생하고 토큰을 삭제한다")
    void refreshFailByTokenMismatch() {
        // given
        String refreshToken = "valid-refresh-token";
        String loginId = "doctor01";

        RefreshToken savedToken = RefreshToken.builder()
                .loginId(loginId)
                .refreshToken("different-token")
                .expiration(3600L)
                .build();

        when(jwtTokenProvider.validateToken(refreshToken)).thenReturn(true);
        when(jwtTokenProvider.getLoginId(refreshToken)).thenReturn(loginId);
        when(refreshTokenRepository.findById(loginId)).thenReturn(Optional.of(savedToken));

        // when & then
        assertThatThrownBy(() -> hospitalStaffService.refresh(refreshToken))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("잘못된 리프레시 토큰입니다.");

        verify(refreshTokenRepository).delete(savedToken);
    }

    @Test
    @DisplayName("리프레시 토큰 갱신 성공 시 새로운 토큰을 반환한다")
    void refreshSuccess() {
        // given
        UUID hospitalId = UUID.randomUUID();
        UUID staffId = UUID.randomUUID();
        String loginId = "doctor01";
        String refreshToken = "valid-refresh-token";

        RefreshToken savedToken = RefreshToken.builder()
                .loginId(loginId)
                .refreshToken(refreshToken)
                .expiration(3600L)
                .build();

        Hospital hospital = Hospital.builder()
                .name("서울병원")
                .address("서울시 강남구")
                .phoneNumber("02-1234-5678")
                .build();
        ReflectionTestUtils.setField(hospital, "hospitalId", hospitalId);

        HospitalStaff staff = HospitalStaff.builder()
                .hospital(hospital)
                .loginId(loginId)
                .name("김의사")
                .staffRole(StaffRole.DOCTOR)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        ReflectionTestUtils.setField(staff, "hospitalStaffId", staffId);

        when(jwtTokenProvider.validateToken(refreshToken)).thenReturn(true);
        when(jwtTokenProvider.getLoginId(refreshToken)).thenReturn(loginId);
        when(refreshTokenRepository.findById(loginId)).thenReturn(Optional.of(savedToken));
        when(hospitalStaffRepository.findByLoginIdAndRecordStatus(loginId, RecordStatus.ACTIVE))
                .thenReturn(Optional.of(staff));
        when(jwtTokenProvider.createAccessToken(anyString(), anyString(), eq("STAFF")))
                .thenReturn("new-access-token");
        when(jwtTokenProvider.createRefreshToken(anyString(), eq("STAFF")))
                .thenReturn("new-refresh-token");

        // when
        StaffTokenResponse response = hospitalStaffService.refresh(refreshToken);

        // then
        assertThat(response.accessToken()).isEqualTo("new-access-token");
        assertThat(response.refreshToken()).isEqualTo("new-refresh-token");
        assertThat(response.staffInfo().hospitalStaffId()).isEqualTo(staffId);
        assertThat(response.staffInfo().name()).isEqualTo("김의사");
        assertThat(response.staffInfo().staffRole()).isEqualTo(StaffRole.DOCTOR);
        verify(refreshTokenRepository, times(1)).save(any(RefreshToken.class));
    }

    @Test
    @DisplayName("리프레시 토큰으로 사용자를 찾지 못하면 UsernameNotFoundException이 발생한다")
    void refreshFailByUserNotFound() {
        // given
        String loginId = "doctor01";
        String refreshToken = "valid-refresh-token";

        RefreshToken savedToken = RefreshToken.builder()
                .loginId(loginId)
                .refreshToken(refreshToken)
                .expiration(3600L)
                .build();

        when(jwtTokenProvider.validateToken(refreshToken)).thenReturn(true);
        when(jwtTokenProvider.getLoginId(refreshToken)).thenReturn(loginId);
        when(refreshTokenRepository.findById(loginId)).thenReturn(Optional.of(savedToken));
        when(hospitalStaffRepository.findByLoginIdAndRecordStatus(loginId, RecordStatus.ACTIVE))
                .thenReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> hospitalStaffService.refresh(refreshToken))
                .isInstanceOf(UsernameNotFoundException.class)
                .hasMessageContaining("사용자를 찾을 수 없습니다.");
    }

    @Test
    @DisplayName("Redis에 리프레시 토큰 정보가 없으면 IllegalArgumentException이 발생한다")
    void refreshFailByNoRedisData() {
        // given
        String refreshToken = "valid-refresh-token";
        String loginId = "doctor01";

        when(jwtTokenProvider.validateToken(refreshToken)).thenReturn(true);
        when(jwtTokenProvider.getLoginId(refreshToken)).thenReturn(loginId);
        when(refreshTokenRepository.findById(loginId)).thenReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> hospitalStaffService.refresh(refreshToken))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("로그인 정보가 없습니다.");
    }

    @Test
    @DisplayName("로그아웃 성공 시 RefreshToken을 삭제하고 AccessToken을 블랙리스트에 추가한다")
    void logoutSuccess() {
        // given
        String accessToken = "valid-access-token";
        String refreshToken = "valid-refresh-token";
        String loginId = "doctor01";

        when(jwtTokenProvider.validateToken(refreshToken)).thenReturn(true);
        when(jwtTokenProvider.getLoginId(refreshToken)).thenReturn(loginId);
        when(jwtTokenProvider.validateToken(accessToken)).thenReturn(true);
        when(jwtTokenProvider.getExpiration(accessToken)).thenReturn(3600000L); // 1시간

        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);

        // when
        hospitalStaffService.logout(accessToken, refreshToken);

        // then
        verify(refreshTokenRepository).deleteById(loginId);
        verify(valueOperations).set(
                eq("blacklist:" + accessToken),
                eq("logout"),
                eq(3600000L),
                eq(TimeUnit.MILLISECONDS)
        );
    }

    @Test
    @DisplayName("로그아웃 시 RefreshToken이 null이면 삭제하지 않고 AccessToken만 블랙리스트에 추가한다")
    void logoutWithNullRefreshToken() {
        // given
        String accessToken = "valid-access-token";

        when(jwtTokenProvider.validateToken(accessToken)).thenReturn(true);
        when(jwtTokenProvider.getExpiration(accessToken)).thenReturn(3600000L);

        ValueOperations<String, String> valueOperations = mock(ValueOperations.class);
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);

        // when
        hospitalStaffService.logout(accessToken, null);

        // then
        verify(refreshTokenRepository, never()).deleteById(anyString());
        verify(valueOperations).set(
                eq("blacklist:" + accessToken),
                eq("logout"),
                eq(3600000L),
                eq(TimeUnit.MILLISECONDS)
        );
    }

    @Test
    @DisplayName("로그아웃 시 AccessToken이 유효하지 않으면 블랙리스트에 추가하지 않는다")
    void logoutWithInvalidAccessToken() {
        // given
        String accessToken = "invalid-access-token";
        String refreshToken = "valid-refresh-token";
        String loginId = "doctor01";

        when(jwtTokenProvider.validateToken(refreshToken)).thenReturn(true);
        when(jwtTokenProvider.getLoginId(refreshToken)).thenReturn(loginId);
        when(jwtTokenProvider.validateToken(accessToken)).thenReturn(false);

        // when
        hospitalStaffService.logout(accessToken, refreshToken);

        // then
        verify(refreshTokenRepository).deleteById(loginId);
        verify(redisTemplate, never()).opsForValue();
    }

    @Test
    @DisplayName("로그아웃 시 AccessToken과 RefreshToken 모두 null이면 아무 작업도 하지 않는다")
    void logoutWithAllNull() {
        // when
        hospitalStaffService.logout(null, null);

        // then
        verify(refreshTokenRepository, never()).deleteById(anyString());
        verify(redisTemplate, never()).opsForValue();
    }
}