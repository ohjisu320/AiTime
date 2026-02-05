package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.assessment.NameNonFacingTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface NameNonFacingTrialRepository extends JpaRepository<NameNonFacingTrial, UUID> {
    Optional<NameNonFacingTrial> findByVideo(Video video);
}
