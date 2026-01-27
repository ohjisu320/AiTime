package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.NameFacingTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface NameFacingTrialRepository extends JpaRepository<NameFacingTrial, UUID> {
}
