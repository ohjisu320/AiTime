//package com.ssafy.aitime.domain.exam.controller;
//
//import com.fasterxml.jackson.databind.ObjectMapper;
//import com.ssafy.aitime.common.response.ApiResponse;
//import com.ssafy.aitime.domain.child.entity.Child;
//import com.ssafy.aitime.domain.child.entity.enums.Gender;
//import com.ssafy.aitime.domain.child.repository.ChildRepository;
//import com.ssafy.aitime.domain.exam.entity.Exam;
//import com.ssafy.aitime.domain.exam.entity.Video;
//import com.ssafy.aitime.domain.exam.entity.assessment.*;
//import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
//import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
//import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
//import com.ssafy.aitime.domain.exam.repository.ExamRepository;
//import com.ssafy.aitime.domain.exam.repository.VideoRepository;
//import com.ssafy.aitime.domain.exam.repository.assessment.*;
//import com.ssafy.aitime.domain.user.entity.User;
//import com.ssafy.aitime.domain.user.entity.enums.UserRole;
//import com.ssafy.aitime.domain.user.repository.UserRepository;
//import com.ssafy.aitime.infra.rabbitmq.dto.message.AnalysisResultMessage;
//import lombok.RequiredArgsConstructor;
//import lombok.extern.slf4j.Slf4j;
//import org.springframework.amqp.rabbit.core.RabbitTemplate;
//import org.springframework.http.HttpStatus;
//import org.springframework.http.ResponseEntity;
//import org.springframework.transaction.annotation.Transactional;
//import org.springframework.web.bind.annotation.*;
//
//import java.time.LocalDate;
//import java.time.LocalDateTime;
//import java.time.format.DateTimeFormatter;
//import java.util.*;
//
//@RestController
//@RequestMapping("/test/rabbitmq")
//@RequiredArgsConstructor
//@Slf4j
//public class RabbitMQTestController {
//
//    private final UserRepository userRepository;
//    private final ChildRepository childRepository;
//    private final ExamRepository examRepository;
//    private final VideoRepository videoRepository;
//
//    // Trial/Event Repositories
//    private final PoseImitationTrialRepository poseImitationTrialRepository;
//    private final PoseImitationEventRepository poseImitationEventRepository;
//    private final SpeechImitationTrialRepository speechImitationTrialRepository;
//    private final SpeechImitationEventRepository speechImitationEventRepository;
//    private final NameFacingTrialRepository nameFacingTrialRepository;
//    private final NameFacingEventRepository nameFacingEventRepository;
//    private final NameNonFacingTrialRepository nameNonFacingTrialRepository;
//    private final NameNonFacingEventRepository nameNonFacingEventRepository;
//
//    private final RabbitTemplate rabbitTemplate;
//    private final ObjectMapper objectMapper;
//
//    /**
//     * 테스트용 Exam + Video 4개 생성
//     */
//    @PostMapping("/setup")
//    @Transactional(timeout = 30) // 30초 타임아웃 설정
//    public ResponseEntity<ApiResponse<Map<String, Object>>> setupTestData() {
//        try {
//            log.info("=== 테스트 데이터 생성 시작 ===");
//
//            // 1. User
//            log.info(">>> User 생성 중...");
//            User user = User.builder()
//                    .loginId("test_" + System.currentTimeMillis())
//                    .password("test1234!")
//                    .name("테스트부모")
//                    .phoneNumber("010-0000-0000")
//                    .userRole(UserRole.USER)
//                    .privacyAgreed(true)
//                    .build();
//            userRepository.save(user);
//            log.info(">>> User 생성 완료: {}", user.getUserId());
//
//            // 2. Child
//            log.info(">>> Child 생성 중...");
//            Child child = Child.builder()
//                    .user(user)
//                    .name("테스트아이")
//                    .birthdate(LocalDate.now().minusMonths(18))
//                    .gender(Gender.MALE)
//                    .build();
//            childRepository.save(child);
//            log.info(">>> Child 생성 완료: {}", child.getChildId());
//
//            // 3. Exam
//            log.info(">>> Exam 생성 중...");
//            Exam exam = Exam.builder()
//                    .child(child)
//                    .examStatus(ExamStatus.IN_PROGRESS)
//                    .submitted(false)
//                    .build();
//            examRepository.save(exam);
//            log.info(">>> Exam 생성 완료: {}", exam.getExamId());
//
//            // 4. Videos
//            log.info(">>> Video 생성 중...");
//            VideoType[] videoTypes = {
//                    VideoType.POSE_IMITATION,
//                    VideoType.SPEECH_IMITATION,
//                    VideoType.NAME_FACING,
//                    VideoType.NAME_NON_FACING
//            };
//
//            Map<String, UUID> videoIds = new HashMap<>();
//            for (int i = 0; i < videoTypes.length; i++) {
//                log.info(">>> Video {} 생성 중: {}", i+1, videoTypes[i]);
//                Video video = Video.builder()
//                        .exam(exam)
//                        .videoType(videoTypes[i])
//                        .s3Bucket("test-bucket")
//                        .s3Key("test-videos/video" + (i + 1) + ".mp4")
//                        .videoStatus(VideoStatus.UPLOADED)
//                        .analysisStatus(null)
//                        .recordedAt(LocalDateTime.now())
//                        .build();
//                videoRepository.save(video);
//                videoIds.put(videoTypes[i].name(), video.getVideoId());
//                log.info(">>> Video {} 생성 완료: {}", i+1, video.getVideoId());
//            }
//
//            log.info("=== 테스트 데이터 생성 완료 ===");
//
//            Map<String, Object> result = new HashMap<>();
//            result.put("userId", user.getUserId());
//            result.put("childId", child.getChildId());
//            result.put("examId", exam.getExamId());
//            result.put("videoIds", videoIds);
//
//            return ResponseEntity.ok(ApiResponse.ok(
//                    "테스트 데이터 생성 완료 - examId: " + exam.getExamId(),
//                    result
//            ));
//
//        } catch (Exception e) {
//            log.error("❌ 테스트 데이터 생성 실패", e);
//            return ResponseEntity.badRequest()
//                    .body(ApiResponse.of(HttpStatus.BAD_REQUEST, "생성 실패: " + e.getMessage(), null));
//        }
//    }
//
//    /**
//     * Task 1: POSE_IMITATION 테스트 메시지 발행
//     */
//    @PostMapping("/publish/task1/{videoId}")
//    public ResponseEntity<ApiResponse<String>> publishTask1Message(@PathVariable UUID videoId) {
//        try {
//            Video video = getVideo(videoId);
//
//            AnalysisResultMessage message = createTask1Message(
//                    video.getExam().getExamId(),
//                    videoId
//            );
//
//            publishMessage(message);
//
//            return ResponseEntity.ok(ApiResponse.ok(
//                    "Task1 (POSE_IMITATION) 메시지 발행 완료",
//                    "RabbitMQ analysis.resp 큐 확인"
//            ));
//        } catch (Exception e) {
//            return ResponseEntity.badRequest().body(
//                    ApiResponse.ok("메시지 발행 실패: " + e.getMessage())
//            );
//        }
//    }
//
//    /**
//     * Task 2: SPEECH_IMITATION 테스트 메시지 발행
//     */
//    @PostMapping("/publish/task2/{videoId}")
//    public ResponseEntity<ApiResponse<String>> publishTask2Message(@PathVariable UUID videoId) {
//        try {
//            Video video = getVideo(videoId);
//
//            AnalysisResultMessage message = createTask2Message(
//                    video.getExam().getExamId(),
//                    videoId
//            );
//
//            publishMessage(message);
//
//            return ResponseEntity.ok(ApiResponse.ok(
//                    "Task2 (SPEECH_IMITATION) 메시지 발행 완료",
//                    "RabbitMQ analysis.resp 큐 확인"
//            ));
//        } catch (Exception e) {
//            return ResponseEntity.badRequest().body(
//                    ApiResponse.ok("메시지 발행 실패: " + e.getMessage())
//            );
//        }
//    }
//
//    /**
//     * Task 3: NAME_FACING 테스트 메시지 발행
//     */
//    @PostMapping("/publish/task3/{videoId}")
//    public ResponseEntity<ApiResponse<String>> publishTask3Message(@PathVariable UUID videoId) {
//        try {
//            Video video = getVideo(videoId);
//
//            AnalysisResultMessage message = createTask3Message(
//                    video.getExam().getExamId(),
//                    videoId
//            );
//
//            publishMessage(message);
//
//            return ResponseEntity.ok(ApiResponse.ok(
//                    "Task3 (NAME_FACING) 메시지 발행 완료",
//                    "RabbitMQ analysis.resp 큐 확인"
//            ));
//        } catch (Exception e) {
//            return ResponseEntity.badRequest().body(
//                    ApiResponse.ok("메시지 발행 실패: " + e.getMessage())
//            );
//        }
//    }
//
//    /**
//     * Task 4: NAME_NON_FACING 테스트 메시지 발행
//     */
//    @PostMapping("/publish/task4/{videoId}")
//    public ResponseEntity<ApiResponse<String>> publishTask4Message(@PathVariable UUID videoId) {
//        try {
//            Video video = getVideo(videoId);
//
//            AnalysisResultMessage message = createTask4Message(
//                    video.getExam().getExamId(),
//                    videoId
//            );
//
//            publishMessage(message);
//
//            return ResponseEntity.ok(ApiResponse.ok(
//                    "Task4 (NAME_NON_FACING) 메시지 발행 완료",
//                    "RabbitMQ analysis.resp 큐 확인"
//            ));
//        } catch (Exception e) {
//            return ResponseEntity.badRequest().body(
//                    ApiResponse.ok("메시지 발행 실패: " + e.getMessage())
//            );
//        }
//    }
//
//    /**
//     * 저장된 결과 조회
//     */
//    @GetMapping("/results/{examId}")
//    @Transactional(readOnly = true)
//    public ResponseEntity<ApiResponse<Map<String, Object>>> getResults(@PathVariable UUID examId) {
//        List<Video> videos = videoRepository.findByExamExamId(examId);
//
//        Map<String, Object> results = new HashMap<>();
//
//        for (Video video : videos) {
//            Map<String, Object> videoResult = new HashMap<>();
//            videoResult.put("videoId", video.getVideoId());
//            videoResult.put("videoType", video.getVideoType());
//            videoResult.put("analysisStatus", video.getAnalysisStatus());
//
//            // Trial/Event 조회
//            switch (video.getVideoType()) {
//                case POSE_IMITATION -> {
//                    Optional<PoseImitationTrial> trial = poseImitationTrialRepository.findByVideo(video);
//                    trial.ifPresent(t -> {
//                        List<PoseImitationEvent> events = poseImitationEventRepository
//                                .findByPoseImitationTrial(t);
//                        videoResult.put("trial", createTrialInfo(t));
//                        videoResult.put("eventCount", events.size());
//                        videoResult.put("events", events.stream().limit(3).toList());
//                    });
//                }
//                case SPEECH_IMITATION -> {
//                    Optional<SpeechImitationTrial> trial = speechImitationTrialRepository.findByVideo(video);
//                    trial.ifPresent(t -> {
//                        List<SpeechImitationEvent> events = speechImitationEventRepository
//                                .findBySpeechImitationTrial(t);
//                        videoResult.put("trial", createTrialInfo(t));
//                        videoResult.put("eventCount", events.size());
//                        videoResult.put("events", events.stream().limit(3).toList());
//                    });
//                }
//                case NAME_FACING -> {
//                    Optional<NameFacingTrial> trial = nameFacingTrialRepository.findByVideo(video);
//                    trial.ifPresent(t -> {
//                        List<NameFacingEvent> events = nameFacingEventRepository
//                                .findByNameFacingTrial(t);
//                        videoResult.put("trial", createTrialInfo(t));
//                        videoResult.put("eventCount", events.size());
//                        videoResult.put("events", events.stream().limit(3).toList());
//                    });
//                }
//                case NAME_NON_FACING -> {
//                    Optional<NameNonFacingTrial> trial = nameNonFacingTrialRepository.findByVideo(video);
//                    trial.ifPresent(t -> {
//                        List<NameNonFacingEvent> events = nameNonFacingEventRepository
//                                .findByNameNonFacingTrial(t);
//                        videoResult.put("trial", createTrialInfo(t));
//                        videoResult.put("eventCount", events.size());
//                        videoResult.put("events", events.stream().limit(3).toList());
//                    });
//                }
//            }
//
//            results.put(video.getVideoType().name(), videoResult);
//        }
//
//        return ResponseEntity.ok(ApiResponse.ok("결과 조회 성공", results));
//    }
//
//    /**
//     * 테스트 데이터 삭제
//     */
//    @DeleteMapping("/cleanup/{examId}")
//    @Transactional
//    public ResponseEntity<ApiResponse<String>> cleanupTestData(@PathVariable UUID examId) {
//        Exam exam = examRepository.findById(examId)
//                .orElseThrow(() -> new IllegalArgumentException("Exam not found"));
//
//        UUID childId = exam.getChild().getChildId();
//        UUID userId = exam.getChild().getUser().getUserId();
//
//        // Exam 삭제 (Video, Trial, Event는 CASCADE로 자동 삭제)
//        examRepository.deleteById(examId);
//
//        // Child 삭제
//        childRepository.deleteById(childId);
//
//        // User 삭제
//        userRepository.deleteById(userId);
//
//        return ResponseEntity.ok(ApiResponse.ok("테스트 데이터 삭제 완료 (CASCADE로 모든 관련 데이터 삭제됨)"));
//    }
//
//    /**
//     * 테스트 가이드
//     */
//    @GetMapping("/guide")
//    public ResponseEntity<ApiResponse<Map<String, Object>>> getTestGuide() {
//        Map<String, Object> guide = new HashMap<>();
//
//        guide.put("step1", "POST /test/rabbitmq/setup - 테스트 데이터 생성");
//        guide.put("step2", "응답에서 examId와 videoIds 확인");
//        guide.put("step3", "POST /test/rabbitmq/publish/task1/{videoId} - Task1 메시지 발행");
//        guide.put("step4", "POST /test/rabbitmq/publish/task2/{videoId} - Task2 메시지 발행");
//        guide.put("step5", "POST /test/rabbitmq/publish/task3/{videoId} - Task3 메시지 발행");
//        guide.put("step6", "POST /test/rabbitmq/publish/task4/{videoId} - Task4 메시지 발행");
//        guide.put("step7", "GET /test/rabbitmq/results/{examId} - 저장된 결과 확인");
//        guide.put("step8", "DELETE /test/rabbitmq/cleanup/{examId} - 데이터 정리");
//
//        Map<String, String> endpoints = new HashMap<>();
//        endpoints.put("테스트 데이터 생성", "POST /test/rabbitmq/setup");
//        endpoints.put("Task1 메시지 발행", "POST /test/rabbitmq/publish/task1/{videoId}");
//        endpoints.put("Task2 메시지 발행", "POST /test/rabbitmq/publish/task2/{videoId}");
//        endpoints.put("Task3 메시지 발행", "POST /test/rabbitmq/publish/task3/{videoId}");
//        endpoints.put("Task4 메시지 발행", "POST /test/rabbitmq/publish/task4/{videoId}");
//        endpoints.put("결과 조회", "GET /test/rabbitmq/results/{examId}");
//        endpoints.put("데이터 정리", "DELETE /test/rabbitmq/cleanup/{examId}");
//
//        guide.put("endpoints", endpoints);
//        guide.put("rabbitmqUI", "http://localhost:15672 (guest/guest)");
//        guide.put("queue", "analysis.resp");
//
//        return ResponseEntity.ok(ApiResponse.ok("테스트 가이드", guide));
//    }
//
//    // ========== Helper Methods ==========
//
//    private Video getVideo(UUID videoId) {
//        return videoRepository.findById(videoId)
//                .orElseThrow(() -> new IllegalArgumentException("Video not found"));
//    }
//
//    private void publishMessage(AnalysisResultMessage message) throws Exception {
//        String json = objectMapper.writeValueAsString(message);
//        rabbitTemplate.convertAndSend("analysis.resp", json);
//    }
//
//    private Map<String, Object> createTrialInfo(Object trial) {
//        Map<String, Object> info = new HashMap<>();
//
//        if (trial instanceof PoseImitationTrial t) {
//            info.put("trialId", t.getPoseImitationTrialId());
//            info.put("adosB6", t.getAdosB6());
//            info.put("adosA8", t.getAdosA8());
//            info.put("adosB18", t.getAdosB18());
//        } else if (trial instanceof SpeechImitationTrial t) {
//            info.put("trialId", t.getSpeechImitationTrialId());
//            info.put("adosA3", t.getAdosA3());
//            info.put("adosB18", t.getAdosB18());
//        } else if (trial instanceof NameFacingTrial t) {
//            info.put("trialId", t.getNameFacingTrialId());
//            info.put("adosB1", t.getAdosB1());
//            info.put("adosB4", t.getAdosB4());
//            info.put("adosB6", t.getAdosB6());
//            info.put("adosB18", t.getAdosB18());
//        } else if (trial instanceof NameNonFacingTrial t) {
//            info.put("trialId", t.getNameNonFacingTrialId());
//            info.put("adosB7", t.getAdosB7());
//            info.put("adosB18", t.getAdosB18());
//        }
//
//        return info;
//    }
//
//    // ========== Message Creation Methods ==========
//
//    private AnalysisResultMessage createTask1Message(UUID examId, UUID videoId) {
//        List<AnalysisResultMessage.TrialMetric> trials = Arrays.asList(
//                createTask1Trial(1, "clapping", true, 0.85, 0.0, 3.0, 4.2, 7.7, 1.2, 3.5, 0.92),
//                createTask1Trial(2, "waving", true, 0.91, 8.0, 11.0, 12.5, 15.8, 1.5, 3.3, 0.95),
//                createTask1Trial(3, "pointing", false, 0.45, 18.0, 21.0, 22.0, 24.0, 1.0, 2.0, 0.70)
//        );
//
//        AnalysisResultMessage.AdosData ados = new AnalysisResultMessage.AdosData();
//        ados.setB6(true);
//        ados.setA8(0);
//        ados.setB18(false);
//
//        return AnalysisResultMessage.builder()
//                .examId(examId)
//                .videoId(videoId)
//                .videoType("POSE_IMITATION")
//                .analyzedAt(LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME))
//                .status("completed")
//                .metrics(new AnalysisResultMessage.MetricsData(trials))
//                .ados(ados)
//                .build();
//    }
//
//    private AnalysisResultMessage.TrialMetric createTask1Trial(
//            int index, String actionType, boolean success, double similarity,
//            double parentStart, double parentEnd, double childStart, double childEnd,
//            double latency, double duration, double attention) {
//
//        AnalysisResultMessage.TrialMetric metric = new AnalysisResultMessage.TrialMetric();
//        metric.setTrialIndex(index);
//        metric.setActionType(actionType);
//        metric.setSuccess(success);
//        metric.setSimilarityScore(similarity);
//        metric.setParentStartTime(parentStart);
//        metric.setParentEndTime(parentEnd);
//        metric.setChildStartTime(childStart);
//        metric.setChildEndTime(childEnd);
//        metric.setLatencyS(latency);
//        metric.setDurationS(duration);
//        metric.setAttentionRatio(attention);
//        return metric;
//    }
//
//    private AnalysisResultMessage createTask2Message(UUID examId, UUID videoId) {
//        List<AnalysisResultMessage.TrialMetric> trials = Arrays.asList(
//                createTask2Trial(1, 0.0, 2.5, "VI12_01", "아", true, 1.12, true, null, false),
//                createTask2Trial(2, 3.0, 5.2, "VI12_02", "엄마", true, 0.95, true, null, false),
//                createTask2Trial(3, 6.0, 8.1, "VI12_03", "응", false, null, false, "no_response", true)
//        );
//
//        AnalysisResultMessage.AdosData ados = new AnalysisResultMessage.AdosData();
//        ados.setA3(1);
//        ados.setB18(true);
//
//        return AnalysisResultMessage.builder()
//                .examId(examId)
//                .videoId(videoId)
//                .videoType("SPEECH_IMITATION")
//                .analyzedAt(LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME))
//                .status("completed")
//                .metrics(new AnalysisResultMessage.MetricsData(trials))
//                .ados(ados)
//                .build();
//    }
//
//    private AnalysisResultMessage.TrialMetric createTask2Trial(
//            int index, double trialStart, double trialEnd, String stimulusId, String stimulusText,
//            boolean responseDetected, Double latency, boolean success, String failureReason, boolean freqAbnormal) {
//
//        AnalysisResultMessage.TrialMetric metric = new AnalysisResultMessage.TrialMetric();
//        metric.setTrialIndex(index);
//        metric.setTrialStartS(trialStart);
//        metric.setTrialEndS(trialEnd);
//        metric.setStimulusId(stimulusId);
//        metric.setStimulusText(stimulusText);
//        metric.setResponseDetected(responseDetected);
//        metric.setLatencyS(latency);
//        metric.setSuccess(success);
//        metric.setFailureReason(failureReason);
//        metric.setFreqAbnormal(freqAbnormal);
//        return metric;
//    }
//
//    private AnalysisResultMessage createTask3Message(UUID examId, UUID videoId) {
//        List<AnalysisResultMessage.TrialMetric> trials = Arrays.asList(
//                createTask3Trial(1, 0.0, 3.5, true, 0.8, 2.5, "smile"),
//                createTask3Trial(2, 4.0, 7.2, true, 1.2, 1.8, "neutral"),
//                createTask3Trial(3, 8.0, 11.5, false, null, 0.0, "neutral")
//        );
//
//        AnalysisResultMessage.AdosData ados = new AnalysisResultMessage.AdosData();
//        ados.setB1(0);
//        ados.setB4(1);
//        ados.setB6(false);
//        ados.setB18(true);
//
//        return AnalysisResultMessage.builder()
//                .examId(examId)
//                .videoId(videoId)
//                .videoType("NAME_FACING")
//                .analyzedAt(LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME))
//                .status("completed")
//                .metrics(new AnalysisResultMessage.MetricsData(trials))
//                .ados(ados)
//                .build();
//    }
//
//    private AnalysisResultMessage.TrialMetric createTask3Trial(
//            int index, double trialStart, double trialEnd, boolean success,
//            Double latency, double gazeDuration, String emotion) {
//
//        AnalysisResultMessage.TrialMetric metric = new AnalysisResultMessage.TrialMetric();
//        metric.setTrialIndex(index);
//        metric.setTrialStartS(trialStart);
//        metric.setTrialEndS(trialEnd);
//        metric.setSuccess(success);
//        metric.setLatencyS(latency);
//        metric.setGazeDurationS(gazeDuration);
//        metric.setEmotion(emotion);
//        return metric;
//    }
//
//    private AnalysisResultMessage createTask4Message(UUID examId, UUID videoId) {
//        List<AnalysisResultMessage.TrialMetric> trials = Arrays.asList(
//                createTask4Trial(1, true, 0.8, 0.0, 1.2, "동한", true, 1.2, 2.5, 1.3, 0.75, false, null, null, null),
//                createTask4Trial(2, true, 1.1, 3.0, 4.5, "동한아", true, 4.5, 6.2, 1.7, 0.82, true, 1.5, 5.2, -2.1),
//                createTask4Trial(3, false, null, 7.0, 8.0, "동한", false, null, null, null, null, false, null, null, null)
//        );
//
//        AnalysisResultMessage.AdosData ados = new AnalysisResultMessage.AdosData();
//        ados.setB7(2);
//        ados.setB18(false);
//
//        return AnalysisResultMessage.builder()
//                .examId(examId)
//                .videoId(videoId)
//                .videoType("NAME_NON_FACING")
//                .analyzedAt(LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME))
//                .status("completed")
//                .metrics(new AnalysisResultMessage.MetricsData(trials))
//                .ados(ados)
//                .build();
//    }
//
//    private AnalysisResultMessage.TrialMetric createTask4Trial(
//            int index, boolean success, Double latency,
//            double triggerStart, double triggerEnd, String triggerText,
//            boolean voiceDetected, Double voiceStart, Double voiceEnd, Double voiceDuration, Double voiceConfidence,
//            boolean gazeMatch, Double gazeDuration, Double headYaw, Double headPitch) {
//
//        AnalysisResultMessage.TrialMetric metric = new AnalysisResultMessage.TrialMetric();
//        metric.setTrialIndex(index);
//        metric.setSuccess(success);
//        metric.setLatencyS(latency);
//        metric.setTriggerStartS(triggerStart);
//        metric.setTriggerEndS(triggerEnd);
//        metric.setTriggerText(triggerText);
//        metric.setVoiceDetected(voiceDetected);
//        metric.setVoiceStartS(voiceStart);
//        metric.setVoiceEndS(voiceEnd);
//        metric.setVoiceDurationS(voiceDuration);
//        metric.setVoiceConfidence(voiceConfidence);
//        metric.setGazeMatch(gazeMatch);
//        metric.setGazeDurationS(gazeDuration);
//        metric.setHeadYawDeg(headYaw);
//        metric.setHeadPitchDeg(headPitch);
//        return metric;
//    }
//}
