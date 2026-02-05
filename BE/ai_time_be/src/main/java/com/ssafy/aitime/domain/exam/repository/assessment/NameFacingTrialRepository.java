package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.assessment.NameFacingTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface NameFacingTrialRepository extends JpaRepository<NameFacingTrial, UUID> {
    Optional<NameFacingTrial> findByVideo(Video video);
}
