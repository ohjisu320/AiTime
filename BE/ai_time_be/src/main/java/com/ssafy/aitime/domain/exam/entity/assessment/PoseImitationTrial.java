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
    @JoinColumn(
            name = "video_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_pose_imitation_video",
                    foreignKeyDefinition = "FOREIGN KEY (video_id) REFERENCES video(video_id) ON DELETE CASCADE"
            )
    )
    private Video video;

    // ADOS 필드 (API에서 수신한 원본 데이터, 추후 서비스 로직에서 수치화)
    @Column(name = "ados_b6", length = 50)
    private String adosB6;  // TRUE/FALSE

    @Column(name = "ados_a8", length = 50)
    private String adosA8;  // 0-3점

    @Column(name = "ados_b18", length = 50)
    private String adosB18;  // TRUE/FALSE

    @Builder
    public PoseImitationTrial(Video video, String adosB6, String adosA8, String adosB18) {
        this.video = video;
        this.adosB6 = adosB6;
        this.adosA8 = adosA8;
        this.adosB18 = adosB18;
    }
}
