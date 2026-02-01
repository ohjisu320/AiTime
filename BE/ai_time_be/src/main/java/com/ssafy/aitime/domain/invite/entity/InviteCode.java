package com.ssafy.aitime.domain.invite.entity;

import com.ssafy.aitime.common.entity.AuditableEntity;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.UuidGenerator;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Entity
@Table(
        name = "invite_code",
        uniqueConstraints = @UniqueConstraint(name = "uk_invite_code_value", columnNames = "invite_code")
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class InviteCode extends AuditableEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "invite_code_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID inviteCodeId; // DB PK (UUID)

    @Column(name = "invite_code", length = 20, nullable = false, updatable = false)
    private String inviteCode; // 비즈니스 식별 코드 (예: FTL-XXXX-XX)

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "hospital_staff_id", nullable = false, foreignKey = @ForeignKey(name = "fk_invite_code_staff"))
    private HospitalStaff hospitalStaff;

    @Column(name = "child_name", nullable = false, length = 50)
    private String childName;

    @Column(name = "child_birthdate", nullable = false)
    private LocalDate childBirthdate;

    @Column(name = "parent_phone", nullable = false, length = 20)
    private String parentPhone;

    @Column(name = "scheduled_at", nullable = false)
    private LocalDateTime scheduledAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "invite_code_status", nullable = false, length = 20)
    private InviteCodeStatus inviteCodeStatus;

    @Column(name = "doctor_id", columnDefinition = "BINARY(16)")
    private UUID doctorId;

    @Builder
    private InviteCode(String inviteCode, HospitalStaff hospitalStaff, String childName, LocalDate childBirthdate,
                       String parentPhone, LocalDateTime scheduledAt, InviteCodeStatus inviteCodeStatus,
                       UUID doctorId) {
        this.inviteCode = inviteCode;
        this.hospitalStaff = hospitalStaff;
        this.childName = childName;
        this.childBirthdate = childBirthdate;
        this.parentPhone = parentPhone;
        this.scheduledAt = scheduledAt;
        this.inviteCodeStatus = (inviteCodeStatus == null) ? InviteCodeStatus.ISSUED : inviteCodeStatus;
        this.doctorId = doctorId;
    }

    public boolean isAlreadyUsed() {
        return this.inviteCodeStatus == InviteCodeStatus.REGISTERED;
    }

    public void markAsUsed() {
        this.inviteCodeStatus = InviteCodeStatus.REGISTERED;
    }

    public void updateStatus(InviteCodeStatus status) {
        this.inviteCodeStatus = status;
    }
}