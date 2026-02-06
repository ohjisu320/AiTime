package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.assessment.PoseImitationTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface PoseImitationTrialRepository extends JpaRepository<PoseImitationTrial, UUID> {
    Optional<PoseImitationTrial> findByVideo(Video video);
}
