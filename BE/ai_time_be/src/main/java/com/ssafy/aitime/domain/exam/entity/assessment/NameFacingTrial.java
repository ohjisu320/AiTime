package com.ssafy.aitime.domain.exam.entity.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "name_facing_trial")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class NameFacingTrial {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "name_facing_trial_id", columnDefinition = "BINARY(16)")
    private UUID nameFacingTrialId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "video_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_name_facing_video",
                    foreignKeyDefinition = "FOREIGN KEY (video_id) REFERENCES video(video_id) ON DELETE CASCADE"
            )
    )
    private Video video;

    // ADOS 필드 (API에서 수신한 원본 데이터, 추후 서비스 로직에서 수치화)
    @Column(name = "ados_b1", length = 50)
    private String adosB1;  // 0-3점

    @Column(name = "ados_b4", length = 50)
    private String adosB4;  // 0-3점

    @Column(name = "ados_b6", length = 50)
    private String adosB6;  // TRUE/FALSE

    @Column(name = "ados_b18", length = 50)
    private String adosB18;  // TRUE/FALSE

    @Builder
    public NameFacingTrial(Video video, String adosB1, String adosB4, String adosB6, String adosB18) {
        this.video = video;
        this.adosB1 = adosB1;
        this.adosB4 = adosB4;
        this.adosB6 = adosB6;
        this.adosB18 = adosB18;
    }
}