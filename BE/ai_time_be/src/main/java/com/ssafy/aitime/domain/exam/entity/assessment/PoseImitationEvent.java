package com.ssafy.aitime.domain.exam.entity.assessment;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "pose_imitation_event")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class PoseImitationEvent {
    @Id @GeneratedValue @UuidGenerator
    @Column(name = "pose_imitation_event_id", columnDefinition = "BINARY(16)")
    private UUID poseImitationEventId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "pose_imitation_trial_id", nullable = false, foreignKey = @ForeignKey(name = "fk_pose_imitation_event_trial"))
    private PoseImitationTrial poseImitationTrial;

    private Integer trialIndex; //시도 번호
    private Boolean responseSuccess;
    private Double similarityScore;
    private Double responseLatencyS;
    private Double durationS;
    private Double attentionRatio;

    @Builder
    public PoseImitationEvent(PoseImitationTrial poseImitationTrial, Integer trialIndex, Boolean responseSuccess,
                              Double similarityScore, Double responseLatencyS, Double durationS, Double attentionRatio) {
        this.poseImitationTrial = poseImitationTrial;
        this.trialIndex = trialIndex;
        this.responseSuccess = responseSuccess;
        this.similarityScore = similarityScore;
        this.responseLatencyS = responseLatencyS;
        this.durationS = durationS;
        this.attentionRatio = attentionRatio;
    }
}
