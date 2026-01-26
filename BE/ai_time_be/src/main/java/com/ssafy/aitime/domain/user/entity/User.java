package com.ssafy.aitime.domain.user.entity;

import com.ssafy.aitime.common.entity.SoftDeletableEntity;
import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.UuidGenerator;

import java.util.UUID;

@Getter
@Entity
@Table(
        name = "users",
        uniqueConstraints = @UniqueConstraint(name = "uk_users_login_id", columnNames = "login_id")
)
@SQLDelete(sql = "UPDATE users SET record_status = 'DELETED', deleted_at = NOW() WHERE user_id = ?")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class User extends SoftDeletableEntity {

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

    @Column(name = "phone_number", length = 20)
    private String phoneNumber;

    @Enumerated(EnumType.STRING)
    @Column(name = "user_role", nullable = false, length = 20)
    private UserRole userRole;

    @Column(name = "privacy_agreed", nullable = false) // 누락된 필드 추가
    private boolean privacyAgreed;

    @Builder
    private User(String loginId, String password, String name, String phoneNumber,
                 UserRole userRole, RecordStatus recordStatus, boolean privacyAgreed) {
        this.loginId = loginId;
        this.password = password;
        this.name = name;
        this.phoneNumber = phoneNumber;
        this.userRole = (userRole == null) ? UserRole.USER : userRole;
        this.recordStatus = (recordStatus == null) ? RecordStatus.ACTIVE : recordStatus;
        this.privacyAgreed = privacyAgreed;
    }

    public void updatePassword(String encryptedPassword) {
        if (encryptedPassword == null || encryptedPassword.isBlank()) {
            throw new IllegalArgumentException("새 비밀번호는 비어있을 수 없습니다.");
        }
        this.password = encryptedPassword;
    }

    public void updateProfile(String name, String phoneNumber) {
        if (name != null && !name.isBlank()) {
            this.name = name;
        }
        if (phoneNumber != null && !phoneNumber.isBlank()) {
            this.phoneNumber = phoneNumber;
        }
    }
}
