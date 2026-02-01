package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.response.HospitalInfoDTO;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface HospitalService {
    /**
     * 자녀와 연동된 병원 목록 조회
     */
    List<HospitalInfoDTO> getLinkedHospitalsByChild(UUID childId);

    /**
     * 자녀와 병원이 이미 연동되어 있는지 확인
     *
     * @param childId 자녀 ID
     * @param hospitalId 병원 ID
     * @return 연동 여부
     */
    boolean isAlreadyLinked(UUID childId, UUID hospitalId);

    /**
     * 자녀와 병원을 연동
     *
     * @param childId 자녀 ID
     * @param hospitalId 병원 ID
     */
    UUID linkChildToHospital(UUID childId, UUID hospitalId);

    /**
     * 특정 아이가 병원과 연동되어 있는지 확인
     * @param childId 아이 ID
     * @return 병원 연동 여부
     */
    boolean hasLinkedHospital(UUID childId);
}
