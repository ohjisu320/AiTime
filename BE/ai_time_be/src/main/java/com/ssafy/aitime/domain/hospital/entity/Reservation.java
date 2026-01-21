package com.ssafy.aitime.domain.hospital.entity;

import com.ssafy.aitime.common.entity.BaseEntity;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.UuidGenerator;

import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Entity
@Table(name = "reservation")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Reservation extends BaseEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "reservation_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID reservationId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "hospital_children_id", nullable = false,
            foreignKey = @ForeignKey(name = "fk_reservation_hospital_children"))
    private HospitalChildren hospitalChildren;

    @Column(name = "scheduled_at", nullable = false)
    private LocalDateTime scheduledAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private ReservationStatus status;

    @Column(name = "cancelled_at")
    private LocalDateTime cancelledAt;

    @Builder
    private Reservation(HospitalChildren hospitalChildren, LocalDateTime scheduledAt,
                        ReservationStatus status, LocalDateTime cancelledAt) {
        this.hospitalChildren = hospitalChildren;
        this.scheduledAt = scheduledAt;
        this.status = (status == null) ? ReservationStatus.SCHEDULED : status;
        this.cancelledAt = cancelledAt;
    }

    public void cancel() {
        this.status = ReservationStatus.CANCELLED;
        this.cancelledAt = LocalDateTime.now();
    }

    public void done() {
        this.status = ReservationStatus.DONE;
    }
}
