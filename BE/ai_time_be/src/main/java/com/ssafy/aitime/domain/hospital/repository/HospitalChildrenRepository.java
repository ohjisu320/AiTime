package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface HospitalChildrenRepository extends JpaRepository<HospitalChildren, UUID> {

    List<HospitalChildren> findByHospitalChildrenIdInAndLinkStatus(
            List<UUID> hospitalChildrenIds,
            LinkStatus linkStatus);
}
