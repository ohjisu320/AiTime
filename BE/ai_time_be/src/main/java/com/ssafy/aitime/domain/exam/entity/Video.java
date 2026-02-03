package com.ssafy.aitime.domain.exam.entity;

import com.ssafy.aitime.common.entity.AuditableEntity;
import com.ssafy.aitime.domain.exam.entity.enums.AnalysisStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
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
@Table(
        name = "video",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_video_exam_type",
                columnNames = {"exam_id", "video_type"}
        )
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Video extends AuditableEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "video_id", columnDefinition = "BINARY(16)")
    private UUID videoId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "exam_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_video_exam",
                    foreignKeyDefinition = "FOREIGN KEY (exam_id) REFERENCES exam(exam_id) ON DELETE CASCADE"
            )
    )
    private Exam exam;

    @Enumerated(EnumType.STRING)
    @Column(name = "video_type", nullable = false, length = 20)
    private VideoType videoType;

    // S3 정보 (물리적 위치 추적용)
    @Column(name = "s3_bucket", length = 63)
    private String s3Bucket;

    @Column(name = "s3_key", nullable = false, length = 255)
    private String s3Key;

    @Column(name = "duration_sec")
    private Integer durationSec;

    @Column(name = "recorded_at")
    private LocalDateTime recordedAt;

    // 비디오 파일 상태
    @Enumerated(EnumType.STRING)
    @Column(name = "video_status", nullable = false, length = 20)
    private VideoStatus videoStatus;

    // 분석 상태
    @Enumerated(EnumType.STRING)
    @Column(name = "analysis_status", length = 20)
    private AnalysisStatus analysisStatus;

    @Column(name = "model_version", length = 50)
    private String modelVersion;

    @Column(name = "analysis_requested_at")
    private LocalDateTime analysisRequestedAt;

    @Column(name = "analysis_completed_at")
    private LocalDateTime analysisCompletedAt;

    @Column(name = "fail_reason", columnDefinition = "TEXT")
    private String failReason;

    @Builder
    private Video(Exam exam, VideoType videoType, String s3Bucket, String s3Key,
                  Integer durationSec, LocalDateTime recordedAt,
                  VideoStatus videoStatus, AnalysisStatus analysisStatus,
                  String modelVersion, LocalDateTime analysisRequestedAt) {
        this.exam = exam;
        this.videoType = videoType;
        this.s3Bucket = s3Bucket;
        this.s3Key = s3Key;
        this.durationSec = durationSec;
        this.recordedAt = recordedAt;
        this.videoStatus = (videoStatus == null) ? VideoStatus.PENDING_UPLOAD : videoStatus;
        this.analysisStatus = analysisStatus;
        this.modelVersion = modelVersion;
        this.analysisRequestedAt = analysisRequestedAt;
    }

    // ========== 비디오 상태 관리 ==========

    /**
     * S3 업로드 완료 처리
     */
    public void markUploaded() {
        this.videoStatus = VideoStatus.UPLOADED;
        this.recordedAt = LocalDateTime.now();
    }

    // ========== 분석 상태 관리 ==========

    /**
     * AI 검사 요청
     */
    public void requestAnalysis(String modelVersion) {
        if (this.videoStatus != VideoStatus.UPLOADED) {
            throw new IllegalStateException("업로드 완료된 비디오만 분석 가능합니다.");
        }
        this.analysisStatus = AnalysisStatus.PENDING;
        this.modelVersion = modelVersion;
        this.analysisRequestedAt = LocalDateTime.now();
        this.failReason = null;
    }

    public void startAnalysis() {
        this.analysisStatus = AnalysisStatus.PROCESSING;
    }

    public void completeAnalysis() {
        this.analysisStatus = AnalysisStatus.SUCCESS;
        this.analysisCompletedAt = LocalDateTime.now();
        this.failReason = null;
    }

    public void failAnalysis(String reason) {
        this.analysisStatus = AnalysisStatus.FAILED;
        this.failReason = reason;
        this.analysisCompletedAt = LocalDateTime.now();
    }

    // ========== 상태 확인 로직 ==========

    public boolean isUploaded() {
        return videoStatus == VideoStatus.UPLOADED;
    }

    public boolean canRequestAnalysis() {
        return videoStatus == VideoStatus.UPLOADED &&
                (analysisStatus == null || analysisStatus == AnalysisStatus.FAILED);
    }

    /**
     * 비디오 soft delete 처리
     */
    public void markDeleted() {
        this.videoStatus = VideoStatus.DELETED;
    }

    /**
     * 삭제 가능 여부 확인
     */
    public boolean canDelete() {
        return videoStatus == VideoStatus.PENDING_UPLOAD
                || videoStatus == VideoStatus.UPLOADED;
    }
}