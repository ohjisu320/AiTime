package com.ssafy.aitime.domain.invite.service;

import com.ssafy.aitime.domain.invite.dto.request.InviteCodeRequest;
import com.ssafy.aitime.domain.invite.dto.response.*;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public interface InviteCodeService {
    /**
     * 초대 코드를 검증하고 필요한 정보만 DTO로 반환합니다.
     *
     * @param inviteCode 검증할 초대 코드
     * @return 검증된 초대 코드 정보 (병원 ID, 병원 엔티티)
     */
    InviteCodeValidationDto validateAndGetInviteCode(String inviteCode);

    /**
     * 초대 코드를 사용 처리합니다.
     *
     * @param inviteCode 사용 처리할 초대 코드 문자열
     */
    void markAsUsed(String inviteCode);

    InviteCodeResponse generateInviteCode(InviteCodeRequest request, UUID hospitalStaffId);
    InviteCodeRevokeResponse revokeInviteCode(UUID inviteCodeId, UUID hospitalStaffId);
    InviteCodeStatusResponse getInviteCodeStatus(UUID inviteCodeId);
    List<UnregisteredPatientResponse> getUnregisteredPatients(UUID hospitalId, int year, int month, int day);
    List<LocalDate> getScheduledDates(UUID hospitalId, int year, int month);
}
