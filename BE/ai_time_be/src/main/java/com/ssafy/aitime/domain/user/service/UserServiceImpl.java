package com.ssafy.aitime.domain.user.service;

import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.TokenResponse;
import com.ssafy.aitime.domain.user.dto.response.UserLoginResponse;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.service.dto.UserInfoDTO;
import com.ssafy.aitime.security.principal.UserPrincipal;
import com.ssafy.aitime.security.provider.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider jwtTokenProvider;

    @Override
    public TokenResponse login(UserLoginRequest userLoginRequest) {
        // 1. 스프링 시큐리티 기본 인증 처리
        UsernamePasswordAuthenticationToken authToken =
                new UsernamePasswordAuthenticationToken(userLoginRequest.loginId(), userLoginRequest.password());

        Authentication authentication = authenticationManager.authenticate(authToken);

        UserPrincipal userPrincipal = (UserPrincipal) authentication.getPrincipal();

        UUID userId = userPrincipal.getUserId();
        String loginId = userPrincipal.getLoginId();
        String name = userPrincipal.getName();
        UserRole role = userPrincipal.getUserRole();

        String accessToken = jwtTokenProvider.createAccessToken(loginId, role.toString());
        String refreshToken = jwtTokenProvider.createRefreshToken(loginId);

        return new TokenResponse(
            accessToken,
            refreshToken,
            new UserInfoDTO(userId, name, role)
        );
    }
}
