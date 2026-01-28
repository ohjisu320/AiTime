package com.ssafy.aitime.domain.hospital.service.dto;

import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;

import java.util.UUID;

public record HospitalStaffInfoDTO(
        UUID hospitalStaffId,
        String name,
        StaffRole staffRole
) {
}
