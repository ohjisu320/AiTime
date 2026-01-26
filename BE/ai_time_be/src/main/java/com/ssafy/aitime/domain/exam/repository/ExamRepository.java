package com.ssafy.aitime.domain.exam.repository;

import com.ssafy.aitime.domain.exam.entity.Exam;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ExamRepository extends JpaRepository<Exam, UUID> {
    // childIds에 해당하는 exam들을 최신순으로 싹 가져옴
    List<Exam> findByChild_ChildIdInOrderByCompletedAtDesc(List<UUID> childIds);
}
