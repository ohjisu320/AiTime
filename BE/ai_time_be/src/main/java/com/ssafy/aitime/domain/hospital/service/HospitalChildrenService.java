package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.response.HospitalResponseDto;

import java.util.List;
import java.util.UUID;

public interface HospitalChildrenService {
    List<HospitalResponseDto> getHospitalResponseDtosByChild(UUID childId);
}
