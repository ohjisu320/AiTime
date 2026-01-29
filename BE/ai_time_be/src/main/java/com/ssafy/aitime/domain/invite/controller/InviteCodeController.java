package com.ssafy.aitime.domain.invite.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.invite.dto.request.InviteCodeRequest;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeResponse;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeRevokeResponse;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeStatusResponse;
import com.ssafy.aitime.domain.invite.dto.response.UnregisteredPatientResponse;
import com.ssafy.aitime.domain.invite.service.InviteCodeService;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

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

    @DeleteMapping("/{inviteCodeId}")
    public ApiResponse<InviteCodeRevokeResponse> revoke(
            @PathVariable UUID inviteCodeId,
            @AuthenticationPrincipal HospitalStaffPrincipal principal
    ) {
        InviteCodeRevokeResponse response = inviteCodeService.revokeInviteCode(inviteCodeId, principal.getHospitalStaffId());
        return ApiResponse.ok("초대코드가 성공적으로 삭제(취소)되었습니다.", response);
    }

    @GetMapping("/{inviteCodeId}/status")
    public ApiResponse<InviteCodeStatusResponse> getStatus(@PathVariable UUID inviteCodeId) {
        InviteCodeStatusResponse response = inviteCodeService.getInviteCodeStatus(inviteCodeId);
        return ApiResponse.ok("초대코드 상태 조회가 완료되었습니다.", response);
    }

    @GetMapping("/patients")
    public ApiResponse<List<UnregisteredPatientResponse>> getUnregisteredPatients(
            @RequestParam int year,
            @RequestParam int month,
            @RequestParam int day,
            @AuthenticationPrincipal HospitalStaffPrincipal principal
    ) {
        List<UnregisteredPatientResponse> patients = inviteCodeService
                .getUnregisteredPatients(principal.getHospitalId(), year, month, day);

        return ApiResponse.ok("날짜별 등록 대기 환아 목록 조회가 완료되었습니다.", patients);
    }
}
