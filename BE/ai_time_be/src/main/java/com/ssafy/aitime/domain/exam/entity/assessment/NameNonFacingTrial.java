package com.ssafy.aitime.domain.exam.entity.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "name_non_facing_trial")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class NameNonFacingTrial {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "name_non_facing_trial_id", columnDefinition = "BINARY(16)")
    private UUID nameNonFacingTrialId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "video_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_name_non_facing_video",
                    foreignKeyDefinition = "FOREIGN KEY (video_id) REFERENCES video(video_id) ON DELETE CASCADE"
            )
    )
    private Video video;

    // ADOS 필드 (API에서 수신한 원본 데이터, 추후 서비스 로직에서 수치화)
    @Column(name = "ados_b7", length = 50)
    private String adosB7;  // 0-3점

    @Column(name = "ados_b18", length = 50)
    private String adosB18;  // TRUE/FALSE

    @Builder
    public NameNonFacingTrial(Video video, String adosB7, String adosB18) {
        this.video = video;
        this.adosB7 = adosB7;
        this.adosB18 = adosB18;
    }
}
