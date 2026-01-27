package com.ssafy.aitime.domain.exam.entity.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "name_facing_trial")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class NameFacingTrial {
    @Id @GeneratedValue @UuidGenerator
    @Column(name = "name_facing_trial_id", columnDefinition = "BINARY(16)")
    private UUID nameFacingTrialId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "video_id", nullable = false, foreignKey = @ForeignKey(name = "fk_name_facing_video"))
    private Video video;

    private Integer totalCallCount;
    private Integer successCount;
    private Double successRate;

    @Builder
    public NameFacingTrial(Video video, Integer totalCallCount, Integer successCount, Double successRate) {
        this.video = video;
        this.totalCallCount = totalCallCount;
        this.successCount = successCount;
        this.successRate = successRate;
    }
}
