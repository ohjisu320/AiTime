package com.ssafy.aitime.domain.exam.repository;

import com.ssafy.aitime.domain.exam.entity.Ados;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface AdosRepository extends JpaRepository<Ados, UUID> {
    /**
     * Exam ID로 ADOS 조회
     */
    Optional<Ados> findByExamExamId(UUID examId);

    /**
     * Exam ID로 ADOS 존재 여부 확인
     */
    boolean existsByExamExamId(UUID examId);
}
