package com.ssafy.aitime.domain.invite.entity;

import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Entity
@Table(name = "invite_code")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class InviteCode {

    @Id
    @Column(name = "invite_code", length = 16, nullable = false, updatable = false)
    private String inviteCode;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "hospital_staff_id", nullable = false, foreignKey = @ForeignKey(name = "fk_invite_code_staff"))
    private HospitalStaff hospitalStaff;

    @Column(name = "child_name", nullable = false, length = 50)
    private String childName;

    @Column(name = "child_birthdate", nullable = false)
    private LocalDate childBirthdate;

    @Column(name = "parent_phone", length = 20)
    private String parentPhone;

    @Column(name = "scheduled_at")
    private LocalDateTime scheduledAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "invite_code_status", nullable = false, length = 20)
    private InviteCodeStatus inviteCodeStatus;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Column(name = "doctor_id", columnDefinition = "BINARY(16)")
    private UUID doctorId;

    @PrePersist
    void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        if (createdAt == null) createdAt = now;
        if (updatedAt == null) updatedAt = now;
        if (inviteCodeStatus == null) inviteCodeStatus = InviteCodeStatus.ISSUED;
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    void updateStatus(InviteCodeStatus status) {
        this.inviteCodeStatus = status;
        onUpdate();
    }

    public boolean isAlreadyUsed() {
        return this.inviteCodeStatus == InviteCodeStatus.REGISTERED;
    }

    public void markAsUsed() {
        this.updateStatus(InviteCodeStatus.REGISTERED);
    }

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
}
