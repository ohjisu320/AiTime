package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.assessment.PoseImitationEvent;
import com.ssafy.aitime.domain.exam.entity.assessment.PoseImitationTrial;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface PoseImitationEventRepository extends JpaRepository<PoseImitationEvent, UUID> {
    List<PoseImitationEvent> findByPoseImitationTrial(PoseImitationTrial trial);
    List<PoseImitationEvent> findByPoseImitationTrialPoseImitationTrialIdOrderByTrialIndex(UUID trialId);
}
