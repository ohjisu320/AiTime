package com.ssafy.aitime.domain.exam.entity;

import com.ssafy.aitime.common.entity.BaseEntity;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
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
@Table(name = "exam")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Exam extends BaseEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "exam_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID examId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "child_id", nullable = false, foreignKey = @ForeignKey(name = "fk_exam_child"))
    private Child child;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private ExamStatus status;

    @Column(name = "isSubmitted", nullable = false)
    private boolean submitted;

    @Column(name = "next_eligible_at")
    private LocalDateTime nextEligibleAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Builder
    private Exam(Child child, ExamStatus status, boolean submitted,
                 LocalDateTime nextEligibleAt, LocalDateTime completedAt) {
        this.child = child;
        this.status = (status == null) ? ExamStatus.IN_PROGRESS : status;
        this.submitted = submitted;
        this.nextEligibleAt = nextEligibleAt;
        this.completedAt = completedAt;
    }

    public void markSubmitted() {
        this.submitted = true;
        this.status = ExamStatus.COMPLETED;
        this.completedAt = LocalDateTime.now();
    }
}
