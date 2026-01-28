package com.ssafy.aitime.domain.hospital.dto.response;

import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import lombok.Builder;

import java.util.UUID;

@Builder
public record HospitalResponseDto(
        UUID hospitalId,       // hospital_id
        String name,           // name
        String address,        // address
        String phoneNumber,    // phone_number
        LinkStatus linkStatus  // hospital_children 테이블의 link_status
) {}