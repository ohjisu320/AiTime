package com.ssafy.aitime.domain.exam.entity.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;



@Getter
@Entity
@Table(name = "pose_imitation_trial")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class PoseImitationTrial {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "pose_imitation_trial_id", columnDefinition = "BINARY(16)")
    private UUID poseImitationTrialId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "video_id", nullable = false, foreignKey = @ForeignKey(name = "fk_pose_imitation_video"))
    private Video video;

    private Integer totalTrialCount;
    private Integer successCount;
    private Double successRate;

    @Builder
    public PoseImitationTrial(Video video, Integer totalTrialCount, Integer successCount, Double successRate) {
        this.video = video;
        this.totalTrialCount = totalTrialCount;
        this.successCount = successCount;
        this.successRate = successRate;
    }
}