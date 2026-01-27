package com.ssafy.aitime.domain.exam.repository;

import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface VideoRepository extends JpaRepository<Video, UUID> {
    /**
     * 특정 검사(Exam)에 연결된 비디오의 총 개수를 반환합니다.
     * SQL: SELECT COUNT(*) FROM video WHERE exam_id = ?
     */
    int countByExam(Exam exam);
}
