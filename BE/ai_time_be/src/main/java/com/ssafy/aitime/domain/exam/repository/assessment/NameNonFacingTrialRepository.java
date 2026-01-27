package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.NameNonFacingTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface NameNonFacingTrialRepository extends JpaRepository<NameNonFacingTrial, UUID> {
}
