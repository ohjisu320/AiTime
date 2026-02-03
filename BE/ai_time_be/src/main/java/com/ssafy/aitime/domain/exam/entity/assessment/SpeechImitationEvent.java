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

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "speech_imitation_event_id", columnDefinition = "BINARY(16)")
    private UUID speechImitationEventId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "speech_imitation_trial_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_speech_imitation_event_trial",
                    foreignKeyDefinition = "FOREIGN KEY (speech_imitation_trial_id) REFERENCES speech_imitation_trial(speech_imitation_trial_id) ON DELETE CASCADE"
            )
    )
    private SpeechImitationTrial speechImitationTrial;

    @Column(name = "trial_index", nullable = false)
    private Integer trialIndex;

    @Column(name = "trial_start_s")
    private Double trialStartS;

    @Column(name = "trial_end_s")
    private Double trialEndS;

    @Column(name = "stimulus_id", length = 50)
    private String stimulusId;

    @Column(name = "stimulus_text", length = 255)
    private String stimulusText;

    @Column(name = "response_detected")
    private Boolean responseDetected;

    @Column(name = "latency_s")
    private Double latencyS;

    @Column(name = "success")
    private Boolean success;

    @Column(name = "failure_reason", length = 255)
    private String failureReason;

    @Column(name = "freq_abnormal")
    private Boolean freqAbnormal;

    @Builder
    public SpeechImitationEvent(SpeechImitationTrial speechImitationTrial, Integer trialIndex,
                                Double trialStartS, Double trialEndS,
                                String stimulusId, String stimulusText,
                                Boolean responseDetected, Double latencyS, Boolean success,
                                String failureReason, Boolean freqAbnormal) {
        this.speechImitationTrial = speechImitationTrial;
        this.trialIndex = trialIndex;
        this.trialStartS = trialStartS;
        this.trialEndS = trialEndS;
        this.stimulusId = stimulusId;
        this.stimulusText = stimulusText;
        this.responseDetected = responseDetected;
        this.latencyS = latencyS;
        this.success = success;
        this.failureReason = failureReason;
        this.freqAbnormal = freqAbnormal;
    }
}
