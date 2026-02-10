package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.response.HospitalResponseDto;

import java.util.List;
import java.util.UUID;

public interface HospitalChildrenService {
    List<HospitalResponseDto> getHospitalResponseDtosByChild(UUID childId);

    /**
     * Child와 Hospital의 연동 여부 확인 (ACTIVE 상태)
     *
     * @param childId 아이 ID
     * @param hospitalId 병원 ID
     * @return 연동되어 있으면 true, 아니면 false
     */
    boolean isChildLinkedToHospital(UUID childId, UUID hospitalId);
}
