package com.ssafy.aitime.domain.exam.entity.assessment;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "speech_imitation_event")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class SpeechImitationEvent {
    @Id @GeneratedValue @UuidGenerator
    @Column(name = "speech_imitation_event_id", columnDefinition = "BINARY(16)")
    private UUID speechImitationEventId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "speech_imitation_trial_id", nullable = false, foreignKey = @ForeignKey(name = "fk_speech_imitation_event_trial"))
    private SpeechImitationTrial speechImitationTrial;

    private Integer trialIndex; //시도 번호
    private Boolean responseDetected;
    private Double latencyS;
    private Boolean success;
    private String failureReason;

    @Builder
    public SpeechImitationEvent(SpeechImitationTrial speechImitationTrial, Integer trialIndex, Boolean responseDetected,
                                Double latencyS, Boolean success, String failureReason) {
        this.speechImitationTrial = speechImitationTrial;
        this.trialIndex = trialIndex;
        this.responseDetected = responseDetected;
        this.latencyS = latencyS;
        this.success = success;
        this.failureReason = failureReason;
    }
}
