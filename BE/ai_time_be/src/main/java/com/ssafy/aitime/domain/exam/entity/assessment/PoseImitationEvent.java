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

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "pose_imitation_event_id", columnDefinition = "BINARY(16)")
    private UUID poseImitationEventId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "pose_imitation_trial_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_pose_imitation_event_trial",
                    foreignKeyDefinition = "FOREIGN KEY (pose_imitation_trial_id) REFERENCES pose_imitation_trial(pose_imitation_trial_id) ON DELETE CASCADE"
            )
    )
    private PoseImitationTrial poseImitationTrial;

    @Column(name = "trial_index", nullable = false)
    private Integer trialIndex;

    @Column(name = "action_type", length = 50)
    private String actionType;

    @Column(name = "success")
    private Boolean success;

    @Column(name = "similarity_score")
    private Double similarityScore;

    // 타임스탬프
    @Column(name = "parent_start_time")
    private Double parentStartTime;

    @Column(name = "parent_end_time")
    private Double parentEndTime;

    @Column(name = "child_start_time")
    private Double childStartTime;

    @Column(name = "child_end_time")
    private Double childEndTime;

    // 수치
    @Column(name = "latency_s")
    private Double latencyS;

    @Column(name = "duration_s")
    private Double durationS;

    // 유효성
    @Column(name = "attention_ratio")
    private Double attentionRatio;

    @Builder
    public PoseImitationEvent(PoseImitationTrial poseImitationTrial, Integer trialIndex,
                              String actionType, Boolean success, Double similarityScore,
                              Double parentStartTime, Double parentEndTime,
                              Double childStartTime, Double childEndTime,
                              Double latencyS, Double durationS, Double attentionRatio) {
        this.poseImitationTrial = poseImitationTrial;
        this.trialIndex = trialIndex;
        this.actionType = actionType;
        this.success = success;
        this.similarityScore = similarityScore;
        this.parentStartTime = parentStartTime;
        this.parentEndTime = parentEndTime;
        this.childStartTime = childStartTime;
        this.childEndTime = childEndTime;
        this.latencyS = latencyS;
        this.durationS = durationS;
        this.attentionRatio = attentionRatio;
    }
}
