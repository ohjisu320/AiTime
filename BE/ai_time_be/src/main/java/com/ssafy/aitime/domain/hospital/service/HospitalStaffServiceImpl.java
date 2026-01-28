package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.hospital.dto.request.HospitalStaffLoginRequest;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalStaffLoginResponse;
import com.ssafy.aitime.domain.hospital.dto.response.StaffTokenResponse;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.repository.HospitalStaffRepository;
import com.ssafy.aitime.domain.hospital.service.dto.HospitalStaffInfoDTO;
import com.ssafy.aitime.domain.user.exception.InvalidPasswordException;
import com.ssafy.aitime.security.entity.RefreshToken;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import com.ssafy.aitime.security.provider.JwtTokenProvider;
import com.ssafy.aitime.security.repository.RefreshTokenRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class HospitalStaffServiceImpl implements HospitalStaffService {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenRepository refreshTokenRepository;
    private final HospitalStaffRepository hospitalStaffRepository;

    @Value("${jwt.refresh-token-expiration}")
    private long refreshTokenExpirationMillis;

    @Override
    @Transactional
    public StaffTokenResponse login(HospitalStaffLoginRequest request) {
        // 1. 스프링 시큐리티 인증 (CustomUserDetailsService가 STAFF 타입으로 조회함)
        Authentication authentication = authenticate(request.loginId(), request.password());
        HospitalStaffPrincipal principal = (HospitalStaffPrincipal) authentication.getPrincipal();

        // 2. 토큰 생성
        String accessToken = jwtTokenProvider.createAccessToken(
                principal.getLoginId(), principal.getStaffRole().name(), "STAFF");
        String refreshToken = jwtTokenProvider.createRefreshToken(principal.getLoginId(), "STAFF");

        // 3. Redis 저장 (RTR 적용)
        saveRefreshToken(principal.getLoginId(), refreshToken);

        return new StaffTokenResponse(
                accessToken,
                refreshToken,
                new HospitalStaffInfoDTO(principal.getHospitalStaffId(), principal.getName(),  principal.getStaffRole()));
    }

    @Override
    @Transactional
    public StaffTokenResponse refresh(String refreshToken) {
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            throw new IllegalArgumentException("유효하지 않은 토큰입니다.");
        }

        String loginId = jwtTokenProvider.getLoginId(refreshToken);
        RefreshToken savedToken = refreshTokenRepository.findById(loginId)
                .orElseThrow(() -> new IllegalArgumentException("로그인 정보가 없습니다."));

        if (!savedToken.getRefreshToken().equals(refreshToken)) {
            refreshTokenRepository.delete(savedToken);
            throw new IllegalArgumentException("잘못된 리프레시 토큰입니다.");
        }

        // DB에서 최신 정보 조회
        HospitalStaff staff = hospitalStaffRepository.findByLoginIdAndRecordStatus(loginId, RecordStatus.ACTIVE)
                .orElseThrow(() -> new UsernameNotFoundException("사용자를 찾을 수 없습니다."));   // TODO: 예외처리 수정

        String newAccessToken = jwtTokenProvider.createAccessToken(loginId, staff.getStaffRole().name(), "STAFF");
        String newRefreshToken = jwtTokenProvider.createRefreshToken(loginId, "STAFF");

        saveRefreshToken(loginId, newRefreshToken);

        return new StaffTokenResponse(
                newAccessToken,
                newRefreshToken,
                new HospitalStaffInfoDTO(staff.getHospitalStaffId(), staff.getName(),  staff.getStaffRole()));
    }

    private void saveRefreshToken(String loginId, String refreshToken) {
        RefreshToken rf = RefreshToken.builder()
                .loginId(loginId)
                .refreshToken(refreshToken)
                .expiration(refreshTokenExpirationMillis / 1000)
                .build();
        refreshTokenRepository.save(rf);
    }

    private Authentication authenticate(String loginId, String password) {
        try {
            // 필터/인터셉터에서 타입을 구분하지 않는다면,
            // 현재 구조상 STAFF 로그인을 하려면 CustomUserDetailsService의 기본 loadUserByUsername이
            // STAFF를 먼저 찾거나 타입 기반 인증이 선행되어야 합니다.
            return authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(loginId, password));
        } catch (BadCredentialsException e) {
            throw new IllegalArgumentException("아이디 또는 비밀번호가 틀렸습니다.");
        }
    }
}
