package com.ssafy.aitime.domain.hospital.entity;

import com.ssafy.aitime.common.entity.BaseEntity;
import com.ssafy.aitime.common.enums.RecordStatus;
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
        name = "hospital",
        uniqueConstraints = @UniqueConstraint(name = "uk_hospital_code", columnNames = "hospital_code")
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Hospital extends BaseEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "hospital_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID hospitalId;

    @Column(name = "hospital_code", nullable = false, length = 100)
    private String hospitalCode;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "address", length = 255)
    private String address;

    @Enumerated(EnumType.STRING)
    @Column(name = "record_status", nullable = false, length = 20)
    private RecordStatus recordStatus;

    @Builder
    private Hospital(String hospitalCode, String name, String address, RecordStatus recordStatus) {
        this.hospitalCode = hospitalCode;
        this.name = name;
        this.address = address;
        this.recordStatus = (recordStatus == null) ? RecordStatus.ACTIVE : recordStatus;
    }
}
