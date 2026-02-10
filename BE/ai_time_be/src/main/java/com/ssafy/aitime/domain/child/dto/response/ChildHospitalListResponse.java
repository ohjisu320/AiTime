package com.ssafy.aitime.domain.child.dto.response;

import com.ssafy.aitime.domain.hospital.dto.response.HospitalResponseDto;

import java.util.List;

public record ChildHospitalListResponse(
        List<HospitalResponseDto> data // 병원 리스트
) {

}
