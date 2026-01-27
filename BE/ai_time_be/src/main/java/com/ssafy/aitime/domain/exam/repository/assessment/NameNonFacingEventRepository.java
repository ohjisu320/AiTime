package com.ssafy.aitime.domain.exam.repository.assessment;

import com.ssafy.aitime.domain.exam.entity.assessment.NameNonFacingEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface NameNonFacingEventRepository extends JpaRepository<NameNonFacingEvent, UUID> {
}
