package com.ssafy.aitime.domain.exam.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import com.ssafy.aitime.domain.exam.service.VideoAnalysisService;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/test/rabbitmq")
@RequiredArgsConstructor
public class RabbitMQTestController {
    private final UserRepository userRepository;
    private final ChildRepository childRepository;
    private final ExamRepository examRepository;
    private final VideoRepository videoRepository;
    private final VideoAnalysisService videoAnalysisService;

    /**
     * 테스트용 Exam + Video 4개 생성
     */
    @PostMapping("/setup")
    public ResponseEntity<ApiResponse<Map<String, Object>>> setupTestData() {
        // 1. 테스트용 User 생성
        User user = User.builder()
                .loginId("test_" + System.currentTimeMillis())
                .password("test1234!")  // 실제로는 암호화 필요하지만 테스트용
                .name("테스트부모")
                .phoneNumber("010-0000-0000")
                .userRole(UserRole.USER)
                .privacyAgreed(true)
                .build();
        userRepository.save(user);

        // 2. 테스트용 Child 생성 (18개월)
        Child child = Child.builder()
                .user(user)
                .name("테스트아이")
                .birthdate(LocalDate.now().minusMonths(18))
                .gender(Gender.MALE)
                .build();
        childRepository.save(child);
        // 1. 임시 Exam 생성
        Exam exam = Exam.builder()
                .child(child)
                .examStatus(ExamStatus.IN_PROGRESS)
                .submitted(false)
                .build();
        examRepository.save(exam);

        // 2. Video 4개 생성
        VideoType[] videoTypes = {
                VideoType.POSE_IMITATION,      // task1: 동작 모방행동
                VideoType.SPEECH_IMITATION,    // task2: 발화 모방행동
                VideoType.NAME_FACING,         // task3: 대면 호명반응
                VideoType.NAME_NON_FACING      // task4: 비대면 호명반응
        };

        for (int i = 0; i < videoTypes.length; i++) {
            Video video = Video.builder()
                    .exam(exam)
                    .videoType(videoTypes[i])
                    .s3Bucket("test-bucket")
                    .s3Key("test-videos/video" + (i + 1) + ".mp4")
                    .videoStatus(VideoStatus.UPLOADED)
                    .analysisStatus(null)
                    .recordedAt(LocalDateTime.now())
                    .build();
            videoRepository.save(video);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("userId", user.getUserId());
        result.put("childId", child.getChildId());
        result.put("examId", exam.getExamId());
        result.put("videoCount", 4);
        result.put("message", "테스트 데이터 생성 완료");


        return ResponseEntity.ok(ApiResponse.ok(
                "테스트 데이터 생성 완료 - examId: " + exam.getExamId(),
                result
        ));
    }

    /**
     * 분석 요청 테스트
     */
    @PostMapping("/analyze/{examId}")
    public ResponseEntity<ApiResponse<String>> testAnalyze(@PathVariable UUID examId) {
        videoAnalysisService.requestAnalysis(examId);
        return ResponseEntity.ok(ApiResponse.ok("분석 요청 완료 - RabbitMQ 큐 확인하세요"));
    }

    /**
     * Exam 상태 조회
     */
    @GetMapping("/status/{examId}")
    @Transactional(readOnly = true)
    public ResponseEntity<ApiResponse<Map<String, Object>>> getStatus(@PathVariable UUID examId) {
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new IllegalArgumentException("Exam not found"));

        List<Video> videos = videoRepository.findByExamExamId(examId);

        Map<String, Object> status = new HashMap<>();
        status.put("examId", exam.getExamId());
        status.put("examStatus", exam.getExamStatus());
        status.put("childName", exam.getChild() != null ? exam.getChild().getName() : "null");
        status.put("childBirthdate", exam.getChild() != null ? exam.getChild().getBirthdate() : null);
        status.put("videoCount", videos.size());


        List<Map<String, Object>> videoStatuses = videos.stream()
                .map(v -> {
                    Map<String, Object> videoInfo = new HashMap<>();
                    videoInfo.put("videoId", v.getVideoId());
                    videoInfo.put("videoType", v.getVideoType());
                    videoInfo.put("videoStatus", v.getVideoStatus());
                    videoInfo.put("analysisStatus", v.getAnalysisStatus());
                    videoInfo.put("s3Uri", "s3://" + v.getS3Bucket() + "/" + v.getS3Key());
                    return videoInfo;
                })
                .toList();

        status.put("videos", videoStatuses);

        return ResponseEntity.ok(ApiResponse.ok("상태 조회 성공", status));
    }

    /**
     * 테스트 데이터 삭제
     */
    @DeleteMapping("/cleanup/{examId}")
    public ResponseEntity<ApiResponse<String>> cleanupTestData(@PathVariable UUID examId) {
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new IllegalArgumentException("Exam not found"));

        UUID childId = exam.getChild().getChildId();
        UUID userId = exam.getChild().getUser().getUserId();

        // Video 삭제 (Trial/Event는 cascade로 자동 삭제될 수 있음)
        List<Video> videos = videoRepository.findByExamExamId(examId);
        videoRepository.deleteAll(videos);

        // Exam 삭제
        examRepository.deleteById(examId);

        // Child 삭제
        childRepository.deleteById(childId);

        // User 삭제
        userRepository.deleteById(userId);

        return ResponseEntity.ok(ApiResponse.ok("테스트 데이터 삭제 완료 (User, Child, Exam, Videos)"));
    }

    /**
     * RabbitMQ 큐 상태 확인 가이드
     */
    @GetMapping("/guide")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getTestGuide() {
        Map<String, Object> guide = new HashMap<>();

        guide.put("step1", "POST /test/rabbitmq/setup - 테스트 데이터 생성");
        guide.put("step2", "POST /test/rabbitmq/analyze/{examId} - 분석 요청");
        guide.put("step3", "http://localhost:15672 - RabbitMQ UI에서 큐 확인");
        guide.put("step4", "GET /test/rabbitmq/status/{examId} - 상태 확인");
        guide.put("step5", "RabbitMQ UI에서 수동으로 결과 메시지 발행");
        guide.put("step6", "GET /test/rabbitmq/status/{examId} - 결과 저장 확인");
        guide.put("step7", "DELETE /test/rabbitmq/cleanup/{examId} - 데이터 정리");

        Map<String, String> queues = new HashMap<>();
        queues.put("요청큐1", "analysis.req.task1 (동작 모방행동)");
        queues.put("요청큐2", "analysis.req.task2 (발화 모방행동)");
        queues.put("요청큐3", "analysis.req.task3 (대면 호명반응)");
        queues.put("요청큐4", "analysis.req.task4 (비대면 호명반응)");
        queues.put("결과큐", "analysis.resp");

        guide.put("queues", queues);
        guide.put("rabbitmqUI", "http://localhost:15672 (guest/guest)");

        return ResponseEntity.ok(ApiResponse.ok("테스트 가이드", guide));
    }
}
