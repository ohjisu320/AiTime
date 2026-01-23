package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface HospitalChildrenRepository extends JpaRepository<HospitalChildren, UUID> {
}
