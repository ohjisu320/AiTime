package com.ssafy.aitime.domain.exam.repository;

import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ExamRepository extends JpaRepository<Exam, UUID> {
    // childIds에 해당하는 exam들을 최신순으로 싹 가져옴
    List<Exam> findByChild_ChildIdInOrderByCompletedAtDesc(List<UUID> childIds);

    // childId에 해당하는 최신 exam 가져옴
    Optional<Exam> findFirstByChild_ChildIdOrderByCreatedAtDesc(UUID childId);

    /**
     * 특정 자녀에게 특정 상태의 검사가 존재하는지 확인합니다.
     * (hasPreviousExam 로직인 ExamStatus.COMPLETED 확인용으로 사용)
     * SQL: SELECT EXISTS(SELECT 1 FROM exam WHERE child_id = ? AND exam_status = ?)
     */
    boolean existsByChild_ChildIdAndExamStatus(UUID childId, ExamStatus examStatus);

    /**
     * 특정 Child의 모든 Exam을 completedAt 기준 내림차순으로 조회
     * (환아별 검사 목록 조회용)
     */
    List<Exam> findByChild_ChildIdOrderByCompletedAtDesc(UUID childId);
}
