package com.ssafy.aitime.domain.user.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.response.TokenResponse;
import com.ssafy.aitime.domain.user.dto.response.UserLoginResponse;
import com.ssafy.aitime.domain.user.service.UserService;
import com.ssafy.aitime.security.provider.JwtTokenProvider;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<UserLoginResponse>> login(@RequestBody @Valid UserLoginRequest userLoginRequest) {

        TokenResponse tokenResponse = userService.login(userLoginRequest);

//        RefreshToken → HttpOnly 쿠키 저장
        ResponseCookie cookie = ResponseCookie
                .from("refreshToken", tokenResponse.refreshToken())
                .httpOnly(true)
                .secure(false)        // HTTPS 환경이면 true로 변경
                .sameSite("Strict")
                .path("/")
                .maxAge(1209600)
                .build();

        UserLoginResponse userLoginResponse = new UserLoginResponse(
                tokenResponse.accessToken(),
                tokenResponse.user()
        );

        return ResponseEntity.ok()
                .header("Set-Cookie", cookie.toString())
                .body(ApiResponse.ok(userLoginResponse));
    }

    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<UserLoginResponse>> refresh(
            @CookieValue(name = "refreshToken") String refreshToken) { // 쿠키에서 추출

        TokenResponse tokenResponse = userService.refresh(refreshToken);

        // 새로운 RefreshToken을 쿠키에 갱신 (기존 설정 유지)
        ResponseCookie cookie = ResponseCookie
                .from("refreshToken", tokenResponse.refreshToken())
                .httpOnly(true)
                .secure(false)
                .sameSite("Strict")
                .path("/")
                .maxAge(1209600)
                .build();

        UserLoginResponse userLoginResponse = new UserLoginResponse(
                tokenResponse.accessToken(),
                tokenResponse.user()
        );

        return ResponseEntity.ok()
                .header("Set-Cookie", cookie.toString())
                .body(ApiResponse.ok(userLoginResponse));
    }

    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Object>> logout(
            @RequestHeader("Authorization") String authHeader,
            @CookieValue(name = "refreshToken") String refreshToken) {

        String accessToken = authHeader.replace("Bearer ", "");
        // 리프레시 토큰이 쿠키에 존재할 때만 서비스 호출
        if (refreshToken != null) {
            userService.logout(accessToken, refreshToken);
        }

        // 쿠키 삭제를 위해 만료시간을 0으로 설정한 쿠키 반환
        ResponseCookie cookie = ResponseCookie.from("refreshToken", "")
                .maxAge(0)
                .path("/")
                .build();

        return ResponseEntity.ok()
                .header("Set-Cookie", cookie.toString())
                .body(ApiResponse.ok("로그아웃 되었습니다."));
    }

}
