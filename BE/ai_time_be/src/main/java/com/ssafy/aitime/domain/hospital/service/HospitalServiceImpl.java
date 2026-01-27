package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.exception.ChildNotFoundException;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalInfoDTO;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.exception.HospitalAlreadyLinkedException;
import com.ssafy.aitime.domain.hospital.exception.HospitalNotFoundException;
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

    private final HospitalChildrenRepository hospitalChildrenRepository;
    private final ChildRepository childRepository;
    private final HospitalRepository hospitalRepository;

    @Override
    @Transactional(readOnly = true)
    public List<HospitalInfoDTO> getLinkedHospitalsByChild(UUID childId) {
        // 1. DB에서 해당 아이와 연결된 병원_아이 엔티티 리스트 조회
        List<HospitalChildren> hospitals = hospitalChildrenRepository.findByChild_ChildIdAndLinkStatus(childId, LinkStatus.ACTIVE);

        // 2. 엔티티 리스트를 HospitalInfo(DTO) 리스트로 변환
        return hospitals.stream()
                .map(hospital -> new HospitalInfoDTO(
                        hospital.getHospital().getHospitalId().toString(),
                        hospital.getHospital().getName()
                ))
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public boolean isAlreadyLinked(UUID childId, UUID hospitalId) {
        return hospitalChildrenRepository
                .existsByChild_ChildIdAndHospital_HospitalIdAndLinkStatus(
                        childId,
                        hospitalId,
                        LinkStatus.ACTIVE
                );
    }

    @Override
    @Transactional
    public void linkChildToHospital(UUID childId, UUID hospitalId) {
        // 1. 중복 연동 확인
        if (isAlreadyLinked(childId, hospitalId)) {
            throw new HospitalAlreadyLinkedException();
        }

        // 2. Child 엔티티 조회
        Child child = childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE)
                .orElseThrow(ChildNotFoundException::new);

        // 3. Hospital 엔티티 조회
        Hospital hospital = hospitalRepository.findById(hospitalId)
                .orElseThrow(HospitalNotFoundException::new);

        // 4. HospitalChildren 생성 및 저장
        HospitalChildren link = HospitalChildren.builder()
                .child(child)
                .hospital(hospital)
                .linkStatus(LinkStatus.ACTIVE)
                .build();

        hospitalChildrenRepository.save(link);
    }
}
