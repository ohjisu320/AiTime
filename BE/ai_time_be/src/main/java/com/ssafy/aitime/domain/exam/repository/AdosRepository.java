package com.ssafy.aitime.domain.exam.repository;

import com.ssafy.aitime.domain.exam.entity.Ados;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
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

    // AdosRepository.java 에 추가
    @Query("SELECT a FROM Ados a " +
            "JOIN FETCH a.exam e " +
            "WHERE e.child.childId = :childId " +
            "AND e.examStatus = 'COMPLETED' " +
            "ORDER BY e.completedAt ASC")
    List<Ados> findAdosHistoryByChildId(@Param("childId") UUID childId);
}
