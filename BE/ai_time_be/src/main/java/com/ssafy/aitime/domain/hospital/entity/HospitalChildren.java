package com.ssafy.aitime.domain.hospital.entity;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.UuidGenerator;
import org.springframework.data.annotation.CreatedDate;

import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Entity
@Table(
        name = "hospital_children",
        uniqueConstraints = @UniqueConstraint(name = "uk_hospital_children", columnNames = {"children_id", "hospital_id"})
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class HospitalChildren {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "hospital_children_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID hospitalChildrenId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "children_id", nullable = false, foreignKey = @ForeignKey(name = "fk_hospital_children_child"))
    private Child child;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "hospital_id", nullable = false, foreignKey = @ForeignKey(name = "fk_hospital_children_hospital"))
    private Hospital hospital;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private LinkStatus status;

    @Column(name = "registered_at", nullable = false, updatable = false)
    private LocalDateTime registeredAt;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @PrePersist
    void onCreate() {
        if (registeredAt == null) registeredAt = LocalDateTime.now();
        if (status == null) status = LinkStatus.ACTIVE;
    }

    @Builder
    private HospitalChildren(Child child, Hospital hospital, LinkStatus status,
                             LocalDateTime registeredAt, LocalDateTime deletedAt) {
        this.child = child;
        this.hospital = hospital;
        this.status = (status == null) ? LinkStatus.ACTIVE : status;
        this.registeredAt = registeredAt;
        this.deletedAt = deletedAt;
    }

    public void unlink() {
        this.status = LinkStatus.INACTIVE;
        this.deletedAt = LocalDateTime.now();
    }
}
