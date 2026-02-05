package com.ssafy.aitime.domain.auth.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.auth.dto.request.PhoneVerificationRequest;
import com.ssafy.aitime.domain.auth.dto.request.PhoneVerifyRequest;
import com.ssafy.aitime.domain.auth.dto.response.PhoneVerificationResponse;
import com.ssafy.aitime.domain.auth.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/phone/verification")
    public ResponseEntity<ApiResponse<PhoneVerificationResponse>> sendCode(@RequestBody PhoneVerificationRequest request) {
        return ResponseEntity.ok(ApiResponse.ok("인증번호가 발송되었습니다.",authService.sendVerificationCode(request.phoneNumber())));
    }

    @PostMapping("/phone/verify")
    public ResponseEntity<ApiResponse<Map<String, Boolean>>> verify(@RequestBody PhoneVerifyRequest request) {
        boolean isVerified = authService.verifyCode(request.phoneNumber(), request.verificationCode());

        return ResponseEntity.ok(ApiResponse.ok("인증 결과입니다.", Map.of("isVerified", isVerified)));
    }
}
