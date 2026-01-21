package com.ssafy.aitime.domain.user.entity;

import com.ssafy.aitime.common.entity.BaseEntity;
import com.ssafy.aitime.common.enums.ActiveDeletedStatus;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
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
        name = "users",
        uniqueConstraints = @UniqueConstraint(name = "uk_users_login_id", columnNames = "login_id")
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class User extends BaseEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "user_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID userId;

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
    private UserRole role;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private ActiveDeletedStatus status;

    @Builder
    private User(String loginId, String password, String name, String email, String phoneNumber,
                 UserRole role, ActiveDeletedStatus status) {
        this.loginId = loginId;
        this.password = password;
        this.name = name;
        this.email = email;
        this.phoneNumber = phoneNumber;
        this.role = (role == null) ? UserRole.USER : role;
        this.status = (status == null) ? ActiveDeletedStatus.ACTIVE : status;
    }
}
