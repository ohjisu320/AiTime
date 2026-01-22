package com.ssafy.aitime.domain.child.entity;

import com.ssafy.aitime.common.entity.SoftDeletableEntity;
import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.UuidGenerator;
import org.hibernate.annotations.Where;

import java.time.LocalDate;
import java.util.UUID;

@Getter
@Entity
@Table(
        name = "child",
        indexes = @Index(name = "idx_child_user_id", columnList = "user_id")
)
@SQLDelete(sql = "UPDATE child SET record_status = 'DELETED', deleted_at = NOW() WHERE child_id = ?")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Child extends SoftDeletableEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "child_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID childId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false, foreignKey = @ForeignKey(name = "fk_child_user"))
    private User user;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    @Column(name = "birthdate", nullable = false)
    private LocalDate birthdate;

    @Enumerated(EnumType.STRING)
    @Column(name = "gender", nullable = false, length = 10)
    private Gender gender;

    @Builder
    private Child(User user, String name, LocalDate birthdate, Gender gender, RecordStatus recordStatus) {
        this.user = user;
        this.name = name;
        this.birthdate = birthdate;
        this.gender = (gender == null) ? Gender.MALE : gender;
        this.recordStatus = (recordStatus == null) ? RecordStatus.ACTIVE : recordStatus;
    }
}
