package com.ssafy.aitime.common.entity;

import com.ssafy.aitime.common.enums.RecordStatus;
import jakarta.persistence.Column;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.MappedSuperclass;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@MappedSuperclass
public class SoftDeletableEntity extends AuditableEntity{

    @Enumerated(EnumType.STRING)
    @Column(name = "record_status", nullable = false, length = 20)
    protected RecordStatus recordStatus = RecordStatus.ACTIVE;

    // delete 시 deletedAt에 날짜 박음
    public void delete() {
        this.recordStatus = RecordStatus.DELETED;
        this.deletedAt = LocalDateTime.now();
    }

    public void restore() {
        this.recordStatus = RecordStatus.ACTIVE;
        this.deletedAt = null;
    }

    public boolean isActive() {
        return this.recordStatus == RecordStatus.ACTIVE;
    }

    public boolean isDeleted() {
        return this.recordStatus == RecordStatus.DELETED;
    }
}
