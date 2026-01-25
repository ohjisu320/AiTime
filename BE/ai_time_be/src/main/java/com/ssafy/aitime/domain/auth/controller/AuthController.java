package com.ssafy.aitime.domain.auth.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.auth.dto.request.PhoneVerificationRequest;
import com.ssafy.aitime.domain.auth.dto.response.PhoneVerificationResponse;
import com.ssafy.aitime.domain.auth.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/phone/verification")
    public ResponseEntity<ApiResponse<PhoneVerificationResponse>> sendCode(@RequestBody PhoneVerificationRequest request) {
        ;

        // Response 구조는 기존에 사용하시던 ApiResponse 형식에 맞추시면 됩니다.
        return ResponseEntity.ok(ApiResponse.ok("인증번호가 발송되었습니다.",authService.sendVerificationCode(request.phoneNumber())));
    }
}
