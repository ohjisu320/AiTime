package com.ssafy.aitime.domain.exam.entity.assessment;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "name_facing_event")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class NameFacingEvent {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "name_facing_event_id", columnDefinition = "BINARY(16)")
    private UUID nameFacingEventId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "name_facing_trial_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_name_facing_event_trial",
                    foreignKeyDefinition = "FOREIGN KEY (name_facing_trial_id) REFERENCES name_facing_trial(name_facing_trial_id) ON DELETE CASCADE"
            )
    )
    private NameFacingTrial nameFacingTrial;

    @Column(name = "trial_index", nullable = false)
    private Integer trialIndex;

    @Column(name = "trial_start_s")
    private Double trialStartS;

    @Column(name = "trial_end_s")
    private Double trialEndS;

    @Column(name = "success")
    private Boolean success;

    @Column(name = "latency_s")
    private Double latencyS;

    @Column(name = "gaze_duration_s")
    private Double gazeDurationS;

    @Column(name = "emotion", length = 50)
    private String emotion;

    @Builder
    public NameFacingEvent(NameFacingTrial nameFacingTrial, Integer trialIndex,
                           Double trialStartS, Double trialEndS,
                           Boolean success, Double latencyS, Double gazeDurationS,
                           String emotion) {
        this.nameFacingTrial = nameFacingTrial;
        this.trialIndex = trialIndex;
        this.trialStartS = trialStartS;
        this.trialEndS = trialEndS;
        this.success = success;
        this.latencyS = latencyS;
        this.gazeDurationS = gazeDurationS;
        this.emotion = emotion;
    }
}

