package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.response.HospitalResponseDto;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class HospitalChildrenServiceImpl implements HospitalChildrenService {

    private final HospitalChildrenRepository hospitalChildrenRepository;

    @Transactional(readOnly = true)
    public List<HospitalResponseDto> getHospitalResponseDtosByChild(UUID childId) {
        // hospital_children 테이블에서 ACTIVE 상태인 연결 정보 조회
        List<HospitalChildren> linkHospitalChildren = hospitalChildrenRepository.findByChild_ChildIdAndLinkStatus(childId, LinkStatus.ACTIVE);

        return linkHospitalChildren.stream()
                .map(link -> HospitalResponseDto.builder()
                        .hospitalId(link.getHospital().getHospitalId())
                        .name(link.getHospital().getName())
                        .address(link.getHospital().getAddress())
                        .phoneNumber(link.getHospital().getPhoneNumber())
                        .linkStatus(link.getLinkStatus())
                        .build())
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public boolean isChildLinkedToHospital(UUID childId, UUID hospitalId) {
        return hospitalChildrenRepository.existsByChild_ChildIdAndHospital_HospitalIdAndLinkStatus(
                childId, hospitalId, LinkStatus.ACTIVE);
    }
}
