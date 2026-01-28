package com.ssafy.aitime.domain.invite.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.invite.dto.request.InviteCodeRequest;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeResponse;
import com.ssafy.aitime.domain.invite.service.InviteCodeService;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/invite-code")
@RequiredArgsConstructor
public class InviteCodeController {

    private final InviteCodeService inviteCodeService;

    @PostMapping
    public ResponseEntity<ApiResponse<InviteCodeResponse>> create(
            @RequestBody @Valid InviteCodeRequest request,
            @AuthenticationPrincipal HospitalStaffPrincipal principal
    ) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created("초대코드가 성공적으로 발급되었습니다.", inviteCodeService.generateInviteCode(request, principal.getHospitalStaffId())));
    }
}
