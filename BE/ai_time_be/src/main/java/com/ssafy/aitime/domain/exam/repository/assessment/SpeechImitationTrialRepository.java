package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.assessment.SpeechImitationTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface SpeechImitationTrialRepository extends JpaRepository<SpeechImitationTrial, UUID> {
    Optional<SpeechImitationTrial> findByVideo(Video video);
}
