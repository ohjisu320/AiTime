package com.ssafy.aitime.domain.exam.entity.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "speech_imitation_trial")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class SpeechImitationTrial {
    @Id @GeneratedValue @UuidGenerator
    @Column(name = "speech_imitation_trial_id", columnDefinition = "BINARY(16)")
    private UUID speechImitationTrialId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "video_id", nullable = false, foreignKey = @ForeignKey(name = "fk_speech_imitation_video"))
    private Video video;

    private String stimulusId;
    private String stimulusText;

    @Builder
    public SpeechImitationTrial(Video video, String stimulusId, String stimulusText) {
        this.video = video;
        this.stimulusId = stimulusId;
        this.stimulusText = stimulusText;
    }
}
