package com.ssafy.aitime.domain.exam.repository;

import com.ssafy.aitime.domain.exam.entity.Analysis;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface AnalysisRepository extends JpaRepository<Analysis, UUID> {
}
