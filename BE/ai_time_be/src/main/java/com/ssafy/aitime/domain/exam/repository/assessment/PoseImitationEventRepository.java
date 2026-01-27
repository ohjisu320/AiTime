package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.PoseImitationEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface PoseImitationEventRepository extends JpaRepository<PoseImitationEvent, UUID> {
}
