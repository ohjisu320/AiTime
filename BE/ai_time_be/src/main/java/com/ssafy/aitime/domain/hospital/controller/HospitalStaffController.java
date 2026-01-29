package com.ssafy.aitime.domain.hospital.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.hospital.dto.request.HospitalStaffLoginRequest;
import com.ssafy.aitime.domain.hospital.dto.response.DoctorListResponse;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalStaffLoginResponse;
import com.ssafy.aitime.domain.hospital.dto.response.StaffTokenResponse;
import com.ssafy.aitime.domain.hospital.service.HospitalStaffService;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/hospital-staff")
@RequiredArgsConstructor
public class HospitalStaffController {

    private final HospitalStaffService hospitalStaffService;

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<HospitalStaffLoginResponse>> login(
            @RequestBody @Valid HospitalStaffLoginRequest loginRequest
    ) {
        // 1. 서비스에서 토큰 세트와 스태프 정보를 담은 StaffTokenResponse 획득
        StaffTokenResponse tokenResponse = hospitalStaffService.login(loginRequest);

        // 2. RefreshToken을 HttpOnly 쿠키로 생성 (UserController와 설정 동일)
        ResponseCookie cookie = createRefreshTokenCookie(tokenResponse.refreshToken());

        // 3. 클라이언트가 사용할 바디 데이터 구성 (명세서 규격)
        HospitalStaffLoginResponse responseBody = new HospitalStaffLoginResponse(
                tokenResponse.accessToken(),
                tokenResponse.staffInfo()
        );

        return ResponseEntity.ok()
                .header("Set-Cookie", cookie.toString())
                .body(ApiResponse.ok("로그인에 성공하였습니다.", responseBody));
    }

    /**
     * 병원 관계자 토큰 재발급
     */
    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<HospitalStaffLoginResponse>> refresh(
            @CookieValue(name = "refreshToken") String refreshToken
    ) {
        // 1. 쿠키에서 받은 RefreshToken으로 토큰 갱신 로직 수행
        StaffTokenResponse tokenResponse = hospitalStaffService.refresh(refreshToken);

        // 2. 갱신된 RefreshToken을 쿠키에 저장
        ResponseCookie cookie = createRefreshTokenCookie(tokenResponse.refreshToken());

        // 3. 갱신된 AccessToken과 스태프 정보 반환
        HospitalStaffLoginResponse responseBody = new HospitalStaffLoginResponse(
                tokenResponse.accessToken(),
                tokenResponse.staffInfo()
        );

        return ResponseEntity.ok()
                .header("Set-Cookie", cookie.toString())
                .body(ApiResponse.ok("토큰이 재발급되었습니다.", responseBody));
    }

    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Object>> logout(
            @RequestHeader(value = "Authorization", required = false) String authHeader,
            @CookieValue(name = "refreshToken", required = false) String refreshToken
    ) {
        String accessToken = resolveBearerToken(authHeader);

        hospitalStaffService.logout(accessToken, refreshToken);

        // 쿠키 삭제를 위해 만료시간을 0으로 설정한 쿠키 반환
        ResponseCookie cookie = ResponseCookie.from("refreshToken", "")
                .maxAge(0)
                .path("/")
                .build();

        return ResponseEntity.ok()
                .header("Set-Cookie", cookie.toString())
                .body(ApiResponse.ok("로그아웃 되었습니다.", null));
    }

    @GetMapping("/doctors")
    public ResponseEntity<ApiResponse<List<DoctorListResponse>>> getDoctors(
            @AuthenticationPrincipal HospitalStaffPrincipal principal
    ) {
        List<DoctorListResponse> response = hospitalStaffService.getDoctorsInMyHospital(principal.getHospitalStaffId());
        return ResponseEntity.ok()
                        .body(ApiResponse.ok("의사 목록 조회가 완료되었습니다.", response));
    }

    /**
     * 쿠키 생성 공통 메서드 (보안 설정 일관성 유지)
     */
    private ResponseCookie createRefreshTokenCookie(String refreshToken) {
        return ResponseCookie.from("refreshToken", refreshToken)
                .httpOnly(true)
                .secure(false)        // HTTPS 운영 환경이면 true로 변경
                .sameSite("Strict")
                .path("/")
                .maxAge(1209600)      // 14일 (UserController 설정과 동일)
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
