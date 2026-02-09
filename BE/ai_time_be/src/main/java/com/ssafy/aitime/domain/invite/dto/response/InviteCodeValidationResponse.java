package com.ssafy.aitime.domain.invite.dto.response;

import com.ssafy.aitime.domain.hospital.entity.Hospital;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 검증된 초대 코드 정보를 담는 DTO
 * 병원 연동에 필요한 최소한의 정보만 포함
 */
public record InviteCodeValidationResponse(
        String inviteCode,        // invite_code (PK)
        UUID hospitalId,          // hospital_id
        LocalDateTime scheduledAt,// scheduled_at
        UUID doctorId             // doctor_id
) {

    /**
     * 정적 팩토리 메서드 패턴
     */
    public static InviteCodeValidationResponse from(
            String inviteCode,
            Hospital hospital,
            LocalDateTime scheduledAt,
            UUID doctorId
    ) {
        return new InviteCodeValidationResponse(
                inviteCode,
                hospital.getHospitalId(),
                scheduledAt,
                doctorId
        );
    }
}
