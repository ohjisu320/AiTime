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

    /**
     * 특정 아이가 병원과 연동되어 있는지 확인 (ACTIVE 상태만)
     * ExamService에서 NEED_HOSPITAL 상태를 판단하기 위해 사용
     */
    boolean existsByChild_ChildIdAndLinkStatus(UUID childId, LinkStatus linkStatus);

    /**
     * 특정 아이가 병원과 연동되어 있는지 확인 (모든 상태)
     * 간단한 체크용
     */
    default boolean existsByChild_ChildId(UUID childId) {
        return existsByChild_ChildIdAndLinkStatus(childId, LinkStatus.ACTIVE);
    }
}
