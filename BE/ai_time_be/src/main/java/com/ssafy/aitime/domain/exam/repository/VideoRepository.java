package com.ssafy.aitime.domain.exam.repository;

import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.AnalysisStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface VideoRepository extends JpaRepository<Video, UUID> {
    /**
     * 특정 검사(Exam)에 연결된 비디오의 총 개수를 반환합니다.
     * SQL: SELECT COUNT(*) FROM video WHERE exam_id = ?
     */
    int countByExam(Exam exam);

    /**
     * 특정 검사(Exam)에 연결된 모든 비디오를 반환합니다.
     * ExamService에서 UPLOADED 상태의 비디오만 필터링하기 위해 사용
     */
    List<Video> findByExam(Exam exam);

    Optional<Video> findByExamExamIdAndVideoType(UUID examId, VideoType videoType);

    List<Video> findByExamExamId(UUID examId);

    @Query("SELECT COUNT(v) FROM Video v " +
            "WHERE v.exam.examId = :examId " +
            "AND v.analysisStatus = :status")
    long countByExamIdAndAnalysisStatus(
            @Param("examId") UUID examId,
            @Param("status") AnalysisStatus status
    );

    List<Video> findByExam_ExamIdInAndVideoStatusNot(List<UUID> examIds, VideoStatus videoStatus);
}
