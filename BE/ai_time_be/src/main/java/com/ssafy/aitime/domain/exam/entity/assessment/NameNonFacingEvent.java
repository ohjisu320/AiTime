package com.ssafy.aitime.domain.exam.entity.assessment;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "name_non_facing_event")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class NameNonFacingEvent {
    @Id @GeneratedValue @UuidGenerator
    @Column(name = "name_non_facing_event_id", columnDefinition = "BINARY(16)")
    private UUID nameNonFacingEventId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "name_non_facing_trial_id", nullable = false, foreignKey = @ForeignKey(name = "fk_name_non_facing_event_trial"))
    private NameNonFacingTrial nameNonFacingTrial;

    private Integer trialIndex; //시도 번호
    private Boolean responseSuccess;
    private Double latencyS;
    private Double gazeDurationS;
    private Double headYawDeg;
    private Double headPitchDeg;

    @Builder
    public NameNonFacingEvent(NameNonFacingTrial nameNonFacingTrial, Integer trialIndex, Boolean responseSuccess,
                              Double latencyS, Double gazeDurationS, Double headYawDeg, Double headPitchDeg) {
        this.nameNonFacingTrial = nameNonFacingTrial;
        this.trialIndex = trialIndex;
        this.responseSuccess = responseSuccess;
        this.latencyS = latencyS;
        this.gazeDurationS = gazeDurationS;
        this.headYawDeg = headYawDeg;
        this.headPitchDeg = headPitchDeg;
    }
}