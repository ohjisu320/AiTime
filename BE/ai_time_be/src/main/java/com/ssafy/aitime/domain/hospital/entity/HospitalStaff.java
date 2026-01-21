package com.ssafy.aitime.domain.hospital.entity;

import com.ssafy.aitime.common.entity.BaseEntity;
import com.ssafy.aitime.common.enums.ActiveDeletedStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.UuidGenerator;

import java.util.UUID;

@Getter
@Entity
@Table(
        name = "hospital_staff",
        uniqueConstraints = @UniqueConstraint(name = "uk_hospital_staff_login_id", columnNames = "login_id"),
        indexes = @Index(name = "idx_hospital_staff_hospital_id", columnList = "hospital_id")
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class HospitalStaff extends BaseEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "hospital_staff_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID hospitalStaffId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "hospital_id", nullable = false, foreignKey = @ForeignKey(name = "fk_hospital_staff_hospital"))
    private Hospital hospital;

    @Column(name = "login_id", nullable = false, length = 100)
    private String loginId;

    @Column(name = "password", nullable = false, length = 255)
    private String password;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    @Column(name = "email", length = 255)
    private String email;

    @Column(name = "phone_number", length = 20)
    private String phoneNumber;

    @Enumerated(EnumType.STRING)
    @Column(name = "role", nullable = false, length = 20)
    private StaffRole role;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private ActiveDeletedStatus status;

    @Builder
    private HospitalStaff(Hospital hospital, String loginId, String password, String name,
                          String email, String phoneNumber, StaffRole role, ActiveDeletedStatus status) {
        this.hospital = hospital;
        this.loginId = loginId;
        this.password = password;
        this.name = name;
        this.email = email;
        this.phoneNumber = phoneNumber;
        this.role = (role == null) ? StaffRole.DESK : role;
        this.status = (status == null) ? ActiveDeletedStatus.ACTIVE : status;
    }
}
