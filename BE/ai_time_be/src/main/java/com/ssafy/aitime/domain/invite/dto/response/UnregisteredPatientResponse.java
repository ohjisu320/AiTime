package com.ssafy.aitime.domain.invite.dto.response;

import com.ssafy.aitime.domain.invite.entity.InviteCode;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.Period;
import java.util.UUID;

public record UnregisteredPatientResponse(
        UUID inviteCodeId,
        String childName,
        Integer childMonths,
        String parentPhone,
        LocalDateTime scheduledAt,
        String status
) {
    /**
     * InviteCode 엔티티로부터 DTO 생성
     *
     * @param inviteCode 초대코드 엔티티
     * @return UnregisteredPatientResponse
     */
    public static UnregisteredPatientResponse from(InviteCode inviteCode) {
        return new UnregisteredPatientResponse(
                inviteCode.getInviteCodeId(),
                inviteCode.getChildName(),
                calculateAgeInMonths(inviteCode.getChildBirthdate()),
                inviteCode.getParentPhone(),
                inviteCode.getScheduledAt(),
                inviteCode.getInviteCodeStatus().name()
        );
    }

    /**
     * 생년월일 기준으로 개월 수 계산
     *
     * @param birthdate 생년월일
     * @return 개월 수
     */
    private static Integer calculateAgeInMonths(LocalDate birthdate) {
        if (birthdate == null) {
            return null;
        }
        return (int) Period.between(birthdate, LocalDate.now()).toTotalMonths();
    }
}
