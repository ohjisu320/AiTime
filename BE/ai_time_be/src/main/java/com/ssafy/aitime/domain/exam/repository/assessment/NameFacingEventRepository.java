package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.NameFacingEvent;
import com.ssafy.aitime.domain.exam.entity.assessment.NameFacingTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface NameFacingEventRepository extends JpaRepository<NameFacingEvent, UUID> {
    List<NameFacingEvent> findByNameFacingTrial(NameFacingTrial trial);
    List<NameFacingEvent> findByNameFacingTrialNameFacingTrialIdOrderByTrialIndex(UUID trialId);
}
