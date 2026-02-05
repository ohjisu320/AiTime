package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.SpeechImitationEvent;
import com.ssafy.aitime.domain.exam.entity.assessment.SpeechImitationTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface SpeechImitationEventRepository extends JpaRepository<SpeechImitationEvent, UUID> {
    List<SpeechImitationEvent> findBySpeechImitationTrial(SpeechImitationTrial trial);
    List<SpeechImitationEvent> findBySpeechImitationTrialSpeechImitationTrialIdOrderByTrialIndex(UUID trialId);
}
