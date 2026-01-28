package com.ssafy.aitime.domain.invite.repository;

import com.ssafy.aitime.domain.invite.entity.InviteCode;
import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
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
}
