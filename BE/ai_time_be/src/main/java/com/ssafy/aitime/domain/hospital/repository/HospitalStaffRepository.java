package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface HospitalStaffRepository extends JpaRepository<HospitalStaff, UUID> {

    /**
     * 의사 ID와 역할, 상태로 존재 여부 확인
     *
     * @param hospitalStaffId 병원 직원 ID
     * @param staffRole 직원 역할 (DOCTOR)
     * @param recordStatus 레코드 상태 (ACTIVE)
     * @return 존재 여부
     */
    boolean existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
            UUID hospitalStaffId,
            StaffRole staffRole,
            RecordStatus recordStatus
    );


}
