package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.child.dto.response.HospitalInfo;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import com.ssafy.aitime.domain.hospital.repository.HospitalRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class HospitalServiceImpl implements HospitalService {

    private final HospitalRepository hospitalRepository;
    private final HospitalChildrenRepository hospitalChildrenRepository;

    @Override
    @Transactional(readOnly = true)
    public List<HospitalInfo> getLinkedHospitalsByChild(UUID childId) {
        // 1. DB에서 해당 아이와 연결된 병원_아이 엔티티 리스트 조회
        List<HospitalChildren> hospitals = hospitalChildrenRepository.findByChild_ChildIdAndLinkStatus(childId, LinkStatus.ACTIVE);

        // 2. 엔티티 리스트를 HospitalInfo(DTO) 리스트로 변환
        return hospitals.stream()
                .map(hospital -> new HospitalInfo(
                        hospital.getHospital().getHospitalId().toString(),
                        hospital.getHospital().getName()
                ))
                .toList();
    }
}
