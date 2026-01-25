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
import com.ssafy.aitime.domain.user.service.dto.UserInfoDTO;
import com.ssafy.aitime.security.entity.RefreshToken;
import com.ssafy.aitime.security.principal.UserPrincipal;
import com.ssafy.aitime.security.provider.JwtTokenProvider;
import com.ssafy.aitime.security.repository.RefreshTokenRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider jwtTokenProvider;
    private final StringRedisTemplate redisTemplate;
    private final PasswordEncoder passwordEncoder;

    private final RefreshTokenRepository refreshTokenRepository;
    private final UserRepository userRepository;

    @Value("${jwt.refresh-token-expiration}") // 밀리초 단위
    private long refreshTokenExpirationMillis;

    @Override
    @Transactional
    public TokenResponse login(UserLoginRequest userLoginRequest) {
        // 1. 스프링 시큐리티 기본 인증 처리
        UsernamePasswordAuthenticationToken authToken =
                new UsernamePasswordAuthenticationToken(userLoginRequest.loginId(), userLoginRequest.password());

        Authentication authentication = authenticate(userLoginRequest.loginId(), userLoginRequest.password());

        UserPrincipal userPrincipal = (UserPrincipal) authentication.getPrincipal();

        UUID userId = userPrincipal.getUserId();
        String loginId = userPrincipal.getLoginId();
        String name = userPrincipal.getName();
        UserRole role = userPrincipal.getUserRole();

        String accessToken = jwtTokenProvider.createAccessToken(loginId, role.toString());
        String refreshToken = jwtTokenProvider.createRefreshToken(loginId);

        // 레디스에 id와
        RefreshToken rf = RefreshToken.builder()
                .loginId(loginId)
                .refreshToken(refreshToken)
                .expiration(refreshTokenExpirationMillis / 1000) // 초 단위로 변환
                .build();

        refreshTokenRepository.save(rf);

        return new TokenResponse(
            accessToken,
            refreshToken,
            new UserInfoDTO(userId, name, role)
        );
    }

    @Override
    @Transactional
    public TokenResponse refresh(String refreshToken) {
        // JWT 유효성 검증
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            throw new IllegalArgumentException("유효하지 않거나 만료된 리프레시 토큰입니다.");
        }

        // 토큰에서 loginId 추출
        String loginId = jwtTokenProvider.getLoginId(refreshToken);

        // Redis에서 저장된 리프레시 토큰 조회
        RefreshToken savedToken = refreshTokenRepository.findById(loginId)
                .orElseThrow(() -> new IllegalArgumentException("로그인 정보가 없습니다. 다시 로그인해주세요."));

        // 전달받은 토큰과 Redis에 저장된 토큰이 일치하는지 확인
        if (!savedToken.getRefreshToken().equals(refreshToken)) {
            // 일치하지 않으면 보안 위협으로 간주하고 레디스 데이터 삭제 (RTR 보호)
            refreshTokenRepository.delete(savedToken);
            throw new IllegalArgumentException("잘못된 리프레시 토큰입니다. 다시 로그인해주세요.");
        }

        // 새로운 Access/Refresh Token 생성
        User user = userRepository.findByLoginIdAndRecordStatus(loginId, RecordStatus.ACTIVE)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        String newAccessToken = jwtTokenProvider.createAccessToken(loginId, user.getUserRole().toString());
        String newRefreshToken = jwtTokenProvider.createRefreshToken(loginId);

        // Redis 정보 갱신 (RTR 적용)
        RefreshToken updatedRf = RefreshToken.builder()
                .loginId(loginId)
                .refreshToken(newRefreshToken)
                .expiration(refreshTokenExpirationMillis / 1000)
                .build();
        refreshTokenRepository.save(updatedRf);

        return new TokenResponse(
                newAccessToken,
                newRefreshToken,
                new UserInfoDTO(user.getUserId(), user.getName(), user.getUserRole())
        );
    }

    @Override
    @Transactional
    public void logout(String accessToken, String refreshToken) {
        // 리프레쉬토큰에서 유저 로그인 아이디 추출
        String loginId = jwtTokenProvider.getLoginId(refreshToken);
        // 레디스에서 해당 토큰 삭제
        refreshTokenRepository.deleteById(loginId);

        // 액세스 토큰 블랙리스트 등록 (남은 유효 시간만큼 저장)
        long expiration = jwtTokenProvider.getExpiration(accessToken);
        if (expiration > 0) {
            redisTemplate.opsForValue().set(
                    "blacklist:" + accessToken,
                    "logout",
                    expiration,
                    TimeUnit.MILLISECONDS
            );
        }
    }

    @Override
    @Transactional()
    public IdDuplicateResponse checkIdDuplicate(String loginId) {
        return new IdDuplicateResponse(userRepository.existsByLoginId(loginId));
    }

    @Override
    @Transactional
    public UserJoinResponse join(UserJoinRequest request) {
        // 휴대폰 인증 여부 최종 확인 (Redis) - postman 테스트 용으로 주석
        String isVerified = redisTemplate.opsForValue().get("AUTH_VERIFIED:" + request.phoneNumber());
        if (isVerified == null || !isVerified.equals("true")) {
            throw new PhoneVerificationRequiredException();
        }

        // 아이디 중복 최종 체크 (API 우회 방지)
        if (userRepository.existsByLoginId(request.loginId())) {
            throw new UserAlreadyExistException();
        }

        // 비밀번호 암호화 및 Entity 생성
        String encodedPassword = passwordEncoder.encode(request.password());

        User user = User.builder()
                .loginId(request.loginId())
                .password(encodedPassword)
                .name(request.name())
                .phoneNumber(request.phoneNumber())
                .privacyAgreed(request.privacyAgreed())
                .userRole(UserRole.USER)
                .build();

        // DB 저장
        User savedUser = userRepository.save(user);

        // 회원가입 성공 후 Redis의 인증 마크 삭제 (재사용 방지)  - postman 테스트 용으로 주석
        redisTemplate.delete("AUTH_VERIFIED:" + request.phoneNumber());

        return new UserJoinResponse(
                savedUser.getUserId(),
                savedUser.getLoginId(),
                savedUser.getName()
        );
    }

    private Authentication authenticate(String loginId, String password) {
        try {
            UsernamePasswordAuthenticationToken authToken =
                    new UsernamePasswordAuthenticationToken(loginId, password);
            return authenticationManager.authenticate(authToken);
        } catch (BadCredentialsException e) {
            // 시큐리티 예외를 커스텀 예외로 전환하여 던짐
            throw new InvalidPasswordException("아이디 또는 비밀번호가 일치하지 않습니다.");
        }
    }
}
