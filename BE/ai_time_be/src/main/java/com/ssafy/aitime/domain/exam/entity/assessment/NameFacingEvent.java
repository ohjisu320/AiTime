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
    @Id @GeneratedValue @UuidGenerator
    @Column(name = "name_facing_event_id", columnDefinition = "BINARY(16)")
    private UUID nameFacingEventId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "name_facing_trial_id", nullable = false, foreignKey = @ForeignKey(name = "fk_name_facing_event_trial"))
    private NameFacingTrial nameFacingTrial;

    private Integer trialIndex; //시도 번호
    private Double trialStartS;
    private Double trialEndS;
    private Boolean success;
    private Double latencyS;
    private Double gazeDurationS;

    @Builder
    public NameFacingEvent(NameFacingTrial nameFacingTrial, Integer trialIndex, Double trialStartS, Double trialEndS,
                           Boolean success, Double latencyS, Double gazeDurationS) {
        this.nameFacingTrial = nameFacingTrial;
        this.trialIndex = trialIndex;
        this.trialStartS = trialStartS;
        this.trialEndS = trialEndS;
        this.success = success;
        this.latencyS = latencyS;
        this.gazeDurationS = gazeDurationS;
    }
}
