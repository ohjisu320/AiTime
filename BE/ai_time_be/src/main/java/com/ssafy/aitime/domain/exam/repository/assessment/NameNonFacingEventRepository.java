package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.NameNonFacingEvent;
import com.ssafy.aitime.domain.exam.entity.assessment.NameNonFacingTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface NameNonFacingEventRepository extends JpaRepository<NameNonFacingEvent, UUID> {
    List<NameNonFacingEvent> findByNameNonFacingTrial(NameNonFacingTrial trial);
    List<NameNonFacingEvent> findByNameNonFacingTrialNameNonFacingTrialIdOrderByTrialIndex(UUID trialId);
}
