package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.SpeechImitationEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface SpeechImitationEventRepository extends JpaRepository<SpeechImitationEvent, UUID> {
}
