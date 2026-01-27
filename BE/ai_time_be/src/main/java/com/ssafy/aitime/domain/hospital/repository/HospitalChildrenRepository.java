package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface HospitalChildrenRepository extends JpaRepository<HospitalChildren, UUID> {

    // hospitalChildrenIds에 해당하는 엔티티 추출
    List<HospitalChildren> findByHospitalChildrenIdInAndLinkStatus(
            List<UUID> hospitalChildrenIds,
            LinkStatus linkStatus);

    // childId가 가진 HospitalChildren 엔티티 추출
    List<HospitalChildren> findByChild_ChildIdAndLinkStatus(
            UUID childId,
            LinkStatus linkStatus
    );

    // 중복 연동 체크
    boolean existsByChild_ChildIdAndHospital_HospitalIdAndLinkStatus(
            UUID childId,
            UUID hospitalId,
            LinkStatus linkStatus
    );
}
