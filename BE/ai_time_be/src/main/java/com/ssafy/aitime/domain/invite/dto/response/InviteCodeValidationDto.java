package com.ssafy.aitime.domain.invite.dto.response;

import com.ssafy.aitime.domain.hospital.entity.Hospital;
import lombok.Builder;
import lombok.Getter;

import java.util.UUID;

/**
 * 검증된 초대 코드 정보를 담는 DTO
 * 병원 연동에 필요한 최소한의 정보만 포함
 */
@Getter
@Builder
public class InviteCodeValidationDto {

    /**
     * 초대 코드 (PK)
     */
    private final String inviteCode;

    /**
     * 병원 ID
     */
    private final UUID hospitalId;

    /**
     * 병원 엔티티 (연동 저장용)
     */
    private final Hospital hospital;

    /**
     * 정적 팩토리 메서드 패턴
     * InviteCode 엔티티로부터 DTO 생성
     */
    public static InviteCodeValidationDto from(
            String inviteCode,
            Hospital hospital
    ) {
        return InviteCodeValidationDto.builder()
                .inviteCode(inviteCode)
                .hospitalId(hospital.getHospitalId())
                .hospital(hospital)
                .build();
    }
}