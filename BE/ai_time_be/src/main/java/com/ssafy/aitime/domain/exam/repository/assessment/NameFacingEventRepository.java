package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.NameFacingEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface NameFacingEventRepository extends JpaRepository<NameFacingEvent, UUID> {
}
