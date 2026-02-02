package com.ssafy.aitime.domain.exam.entity;

import com.ssafy.aitime.common.entity.AuditableEntity;
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
public class Exam extends AuditableEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "exam_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID examId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "child_id", nullable = false, foreignKey = @ForeignKey(name = "fk_exam_child"))
    private Child child;

    @Enumerated(EnumType.STRING)
    @Column(name = "exam_status", nullable = false, length = 20)
    private ExamStatus examStatus;

    @Column(name = "is_submitted", nullable = false)
    private boolean submitted;

    @Column(name = "exam_started_at")
    private LocalDateTime examStartedAt;

    @Column(name = "next_eligible_at")
    private LocalDateTime nextEligibleAt;

    @Column(name = "draft_expires_at")
    private LocalDateTime draftExpiresAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Builder
    private Exam(Child child, ExamStatus examStatus, boolean submitted,
                 LocalDateTime examStartedAt, LocalDateTime nextEligibleAt,
                 LocalDateTime draftExpiresAt, LocalDateTime completedAt) {
        this.child = child;
        this.examStatus = (examStatus == null) ? ExamStatus.IN_PROGRESS : examStatus;
        this.submitted = submitted;
        this.examStartedAt = examStartedAt;
        this.nextEligibleAt = nextEligibleAt;
        this.draftExpiresAt = draftExpiresAt;
        this.completedAt = completedAt;
    }

    /**
     * 첫 비디오 업로드 시 검사 시작 처리
     * examStartedAt과 draftExpiresAt 설정
     */
    public void startExam() {
        if (this.examStartedAt == null) {
            this.examStartedAt = LocalDateTime.now();
            this.draftExpiresAt = this.examStartedAt.plusDays(3);
        }
    }

    /**
     * 검사 완료 시 다음 검사 가능일 설정 (3개월 후)
     */
    public void updateNextEligibleDate(LocalDateTime lastRecordedAt) {
        if (lastRecordedAt == null) {
            this.nextEligibleAt = LocalDateTime.now().plusMonths(3);
        } else {
            this.nextEligibleAt = lastRecordedAt.plusMonths(3);
        }
    }

    public void markSubmitted(LocalDateTime lastRecordedAt) {
        this.submitted = true;
        this.examStatus = ExamStatus.COMPLETED;
        this.completedAt = LocalDateTime.now();
        updateNextEligibleDate(lastRecordedAt); // 다음 검사 가능일 자동 설정
    }
}
