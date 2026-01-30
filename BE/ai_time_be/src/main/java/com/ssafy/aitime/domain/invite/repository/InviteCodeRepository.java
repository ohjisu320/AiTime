package com.ssafy.aitime.domain.invite.repository;

import com.ssafy.aitime.domain.invite.entity.InviteCode;
import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import io.lettuce.core.dynamic.annotation.Param;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface InviteCodeRepository extends JpaRepository<InviteCode, UUID> {
    Optional<InviteCode> findByInviteCode(String inviteCode);
    boolean existsByInviteCode(String inviteCode);
    Optional<InviteCode> findByChildNameAndChildBirthdateAndParentPhoneAndInviteCodeStatusAndDoctorId(
            String childName,
            LocalDate childBirthdate,
            String parentPhone,
            InviteCodeStatus status,
            UUID doctorId
    );
    @Query("""
        SELECT ic FROM InviteCode ic
        JOIN FETCH ic.hospitalStaff hs
        WHERE hs.hospital.hospitalId = :hospitalId
        AND ic.inviteCodeStatus = 'ISSUED'
        AND DATE(ic.scheduledAt) = :targetDate
        ORDER BY ic.scheduledAt ASC
    """)
    List<InviteCode> findUnregisteredPatientsByHospitalAndDate(
            @Param("hospitalId") UUID hospitalId,
            @Param("targetDate") LocalDate targetDate
    );

    @Query("""
        SELECT DISTINCT CAST(ic.scheduledAt AS date)
        FROM InviteCode ic
        JOIN ic.hospitalStaff hs
        WHERE hs.hospital.hospitalId = :hospitalId
        AND ic.inviteCodeStatus = 'ISSUED'
        AND ic.scheduledAt >= :startOfMonth
        AND ic.scheduledAt < :endOfMonth
        ORDER BY CAST(ic.scheduledAt AS date) ASC
    """)
    List<LocalDate> findScheduledDatesByHospitalAndMonth(
            @Param("hospitalId") UUID hospitalId,
            @Param("startOfMonth") LocalDateTime startOfMonth,
            @Param("endOfMonth") LocalDateTime endOfMonth
    );
}
