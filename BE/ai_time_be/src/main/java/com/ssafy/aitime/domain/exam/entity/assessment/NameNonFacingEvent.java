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

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "name_non_facing_event_id", columnDefinition = "BINARY(16)")
    private UUID nameNonFacingEventId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "name_non_facing_trial_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_name_non_facing_event_trial",
                    foreignKeyDefinition = "FOREIGN KEY (name_non_facing_trial_id) REFERENCES name_non_facing_trial(name_non_facing_trial_id) ON DELETE CASCADE"
            )
    )
    private NameNonFacingTrial nameNonFacingTrial;

    @Column(name = "trial_index", nullable = false)
    private Integer trialIndex;

    @Column(name = "success")
    private Boolean success;

    @Column(name = "latency_s")
    private Double latencyS;

    // 트리거 정보
    @Column(name = "trigger_start_s")
    private Double triggerStartS;

    @Column(name = "trigger_end_s")
    private Double triggerEndS;

    @Column(name = "trigger_text", length = 100)
    private String triggerText;

    // 음성 반응 정보
    @Column(name = "voice_detected")
    private Boolean voiceDetected;

    @Column(name = "voice_start_s")
    private Double voiceStartS;

    @Column(name = "voice_end_s")
    private Double voiceEndS;

    @Column(name = "voice_duration_s")
    private Double voiceDurationS;

    @Column(name = "voice_confidence")
    private Double voiceConfidence;

    // 시선 정보
    @Column(name = "gaze_match")
    private Boolean gazeMatch;

    @Column(name = "gaze_duration_s")
    private Double gazeDurationS;

    @Column(name = "head_yaw_deg")
    private Double headYawDeg;

    @Column(name = "head_pitch_deg")
    private Double headPitchDeg;

    @Builder
    public NameNonFacingEvent(NameNonFacingTrial nameNonFacingTrial, Integer trialIndex,
                              Boolean success, Double latencyS,
                              Double triggerStartS, Double triggerEndS, String triggerText,
                              Boolean voiceDetected, Double voiceStartS, Double voiceEndS,
                              Double voiceDurationS, Double voiceConfidence,
                              Boolean gazeMatch, Double gazeDurationS,
                              Double headYawDeg, Double headPitchDeg) {
        this.nameNonFacingTrial = nameNonFacingTrial;
        this.trialIndex = trialIndex;
        this.success = success;
        this.latencyS = latencyS;
        this.triggerStartS = triggerStartS;
        this.triggerEndS = triggerEndS;
        this.triggerText = triggerText;
        this.voiceDetected = voiceDetected;
        this.voiceStartS = voiceStartS;
        this.voiceEndS = voiceEndS;
        this.voiceDurationS = voiceDurationS;
        this.voiceConfidence = voiceConfidence;
        this.gazeMatch = gazeMatch;
        this.gazeDurationS = gazeDurationS;
        this.headYawDeg = headYawDeg;
        this.headPitchDeg = headPitchDeg;
    }
}