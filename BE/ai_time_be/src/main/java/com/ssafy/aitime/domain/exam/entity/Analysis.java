package com.ssafy.aitime.domain.exam.entity;

import com.ssafy.aitime.domain.exam.entity.enums.AnalysisStatus;
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
        name = "analysis",
        uniqueConstraints = @UniqueConstraint(name = "uk_analysis_video", columnNames = "video_id")
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Analysis {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "analysis_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID analysisId;

    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "video_id", nullable = false, foreignKey = @ForeignKey(name = "fk_analysis_video"))
    private Video video;

    @Enumerated(EnumType.STRING)
    @Column(name = "analysis_status", nullable = false, length = 20)
    private AnalysisStatus analysisStatus;

    @Column(name = "model_version", length = 50)
    private String modelVersion;

    @Column(name = "requested_at", nullable = false, updatable = false)
    private LocalDateTime requestedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Column(name = "fail_reason", length = 255)
    private String failReason;

    @PrePersist
    void onCreate() {
        if (requestedAt == null) requestedAt = LocalDateTime.now();
        if (analysisStatus == null) analysisStatus = AnalysisStatus.PENDING;
    }

    @Builder
    private Analysis(Video video, AnalysisStatus analysisStatus, String modelVersion,
                     LocalDateTime requestedAt, LocalDateTime completedAt, String failReason) {
        this.video = video;
        this.analysisStatus = (analysisStatus == null) ? AnalysisStatus.PENDING : analysisStatus;
        this.modelVersion = modelVersion;
        this.requestedAt = requestedAt;
        this.completedAt = completedAt;
        this.failReason = failReason;
    }

    public void markProcessing() { this.analysisStatus = AnalysisStatus.PROCESSING; }
    public void markSuccess() { this.analysisStatus = AnalysisStatus.SUCCESS; this.completedAt = LocalDateTime.now(); }
    public void markFailed(String reason) {
        this.analysisStatus = AnalysisStatus.FAILED;
        this.failReason = reason;
        this.completedAt = LocalDateTime.now();
    }
}
