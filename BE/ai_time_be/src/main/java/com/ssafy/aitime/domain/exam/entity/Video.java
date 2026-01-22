package com.ssafy.aitime.domain.exam.entity;

import com.ssafy.aitime.common.entity.AuditableEntity;
import com.ssafy.aitime.common.entity.BaseEntity;
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
        uniqueConstraints = @UniqueConstraint(name = "uk_video_exam_type", columnNames = {"exam_id", "video_type"})
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Video extends AuditableEntity {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "video_id", columnDefinition = "BINARY(16)", updatable = false, nullable = false)
    private UUID videoId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "exam_id", nullable = false, foreignKey = @ForeignKey(name = "fk_video_exam"))
    private Exam exam;

    @Enumerated(EnumType.STRING)
    @Column(name = "video_type", nullable = false, length = 20)
    private VideoType videoType;

    @Column(name = "s3_bucket", length = 63)
    private String s3Bucket;

    @Column(name = "s3_key", nullable = false, length = 255)
    private String s3Key;

    @Column(name = "duration_sec")
    private Integer durationSec;

    @Column(name = "recorded_at")
    private LocalDateTime recordedAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "video_status", nullable = false, length = 20)
    private VideoStatus videoStatus;

    @Builder
    private Video(Exam exam, VideoType videoType, String s3Bucket, String s3Key,
                  Integer durationSec, LocalDateTime recordedAt, VideoStatus videoStatus) {
        this.exam = exam;
        this.videoType = videoType;
        this.s3Bucket = s3Bucket;
        this.s3Key = s3Key;
        this.durationSec = durationSec;
        this.recordedAt = recordedAt;
        this.videoStatus = (videoStatus == null) ? VideoStatus.UPLOADED : videoStatus;
    }

    public void markAnalyzing() { this.videoStatus = VideoStatus.ANALYZING; }
    public void markFailed() { this.videoStatus = VideoStatus.FAILED; }
}
