package com.ssafy.aitime.domain.user.controller;

import com.ssafy.aitime.common.config.CookieProperties;
import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.user.dto.request.PasswordResetRequest;
import com.ssafy.aitime.domain.user.dto.request.UserJoinRequest;
import com.ssafy.aitime.domain.user.dto.request.UserLoginRequest;
import com.ssafy.aitime.domain.user.dto.request.UserUpdateRequest;
import com.ssafy.aitime.domain.user.dto.response.*;
import com.ssafy.aitime.domain.user.service.UserService;
import com.ssafy.aitime.security.principal.UserPrincipal;
import com.ssafy.aitime.security.provider.JwtTokenProvider;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;
    private final CookieProperties cookieProperties;

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<UserLoginResponse>> login(@RequestBody @Valid UserLoginRequest userLoginRequest) {

        TokenResponse tokenResponse = userService.login(userLoginRequest);

//        RefreshToken → HttpOnly 쿠키 저장
        ResponseCookie cookie = createRefreshTokenCookie(tokenResponse.refreshToken());


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
        ResponseCookie cookie = createRefreshTokenCookie(tokenResponse.refreshToken());

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
            @RequestHeader(value = "Authorization", required = false) String authHeader,
            @CookieValue(name = "refreshToken", required = false) String refreshToken) {

        String accessToken = resolveBearerToken(authHeader);

        userService.logout(accessToken, refreshToken);
        // 쿠키 삭제를 위해 만료시간을 0으로 설정한 쿠키 반환
        ResponseCookie cookie = createExpiredRefreshTokenCookie();

        return ResponseEntity.ok()
                .header("Set-Cookie", cookie.toString())
                .body(ApiResponse.ok("로그아웃 되었습니다.", null));
    }

    @GetMapping("/duplicate-id")
    public ResponseEntity<ApiResponse<IdDuplicateResponse>> checkDuplicate(
            @RequestParam("loginId") String loginId
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok("아이디 중복 확인이 완료되었습니다.", userService.checkIdDuplicate(loginId)));
    }

    @PostMapping("/join")
    public ResponseEntity<ApiResponse<UserJoinResponse>> join(
            @Valid @RequestBody UserJoinRequest request
    ) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created("회원가입이 성공적으로 완료되었습니다.", userService.join(request)));
    }

    @GetMapping("/get-id")
    public ResponseEntity<ApiResponse<IdFindResponse>> getId(@RequestParam("phoneNumber") String phoneNumber) {
        return ResponseEntity.ok(ApiResponse.ok("아이디 조회가 완료되었습니다.", userService.getIdByPhone(phoneNumber)));
    }

    @GetMapping("/verify-identity")
    public ResponseEntity<ApiResponse<UserIdentityResponse>> verifyIdentity(
            @RequestParam("phoneNumber") String phoneNumber) {
        return ResponseEntity.ok(ApiResponse.ok("본인 확인에 성공하였습니다.", userService.verifyUserIdentity(phoneNumber)));
    }

    @PatchMapping("/password")
    public ResponseEntity<ApiResponse<PasswordResetResponse>> resetPassword(
            @Valid @RequestBody PasswordResetRequest request
    ) {
        return ResponseEntity.ok(ApiResponse.ok("비밀번호가 성공적으로 변경되었습니다.", userService.resetPassword(request)));
    }

    @GetMapping("/me")
    public ResponseEntity<ApiResponse<UserMeResponse>> getMyInfo(
            @AuthenticationPrincipal UserPrincipal userPrincipal
    ) {
        return ResponseEntity.ok(ApiResponse.ok("사용자 정보 조회가 완료되었습니다.", userService.getUserInfo(userPrincipal.getUserId())));
    }

    @PatchMapping("/me")
    public ResponseEntity<ApiResponse<UserUpdateResponse>> updateMyInfo(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Valid @RequestBody UserUpdateRequest request
    ) {
        return ResponseEntity.ok(ApiResponse.ok("사용자 정보가 성공적으로 수정되었습니다.", userService.updateUserInfo(userPrincipal.getUserId(), request)));
    }

    @DeleteMapping
    public ResponseEntity<ApiResponse<Void>> withdraw(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestHeader(value = "Authorization", required = false) String authorizationHeader,
            @CookieValue(value = "refreshToken", required = false) String refreshToken,
            HttpServletResponse response
    ) {
        String accessToken = resolveBearerToken(authorizationHeader);

        userService.withdraw(principal.getUserId(), accessToken, refreshToken);

        ResponseCookie expiredCookie = createExpiredRefreshTokenCookie();

        return ResponseEntity.ok()
                .header("Set-Cookie", expiredCookie.toString())
                .body(ApiResponse.ok("회원 탈퇴가 완료되었습니다. 그동안 이용해 주셔서 감사합니다.", null));
    }

    private ResponseCookie createRefreshTokenCookie(String refreshToken) {
        return ResponseCookie
                .from(cookieProperties.getName(), refreshToken)
                .httpOnly(cookieProperties.isHttpOnly())
                .secure(cookieProperties.isSecure())
                .sameSite(cookieProperties.getSameSite())
                .path(cookieProperties.getPath())
                .maxAge(cookieProperties.getMaxAge())
                .build();
    }

    private ResponseCookie createExpiredRefreshTokenCookie() {
        return ResponseCookie
                .from(cookieProperties.getName(), "")
                .httpOnly(cookieProperties.isHttpOnly())
                .secure(cookieProperties.isSecure())
                .sameSite(cookieProperties.getSameSite())
                .path(cookieProperties.getPath())
                .maxAge(0)
                .build();
    }

    private String resolveBearerToken(String authorizationHeader) {
        if (authorizationHeader == null || authorizationHeader.isBlank()) {
            return null;
        }
        if (!authorizationHeader.startsWith("Bearer ")) {
            return null;
        }
        return authorizationHeader.substring(7);
    }

}