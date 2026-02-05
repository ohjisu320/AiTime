package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.ChildHomeStatus;
import com.ssafy.aitime.domain.exam.dto.response.AdosDetailResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamInfoResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamStartResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryDTO;
import com.ssafy.aitime.domain.exam.entity.Ados;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import com.ssafy.aitime.domain.exam.exception.ExamNotEligibleException;
import com.ssafy.aitime.domain.exam.exception.ExamNotFoundException;
import com.ssafy.aitime.domain.exam.repository.AdosRepository;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import com.ssafy.aitime.domain.hospital.dto.response.AdosReportGraphsResponse;
import com.ssafy.aitime.domain.hospital.service.HospitalService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ExamServiceImpl implements ExamService {

    private final ExamRepository examRepository;
    private final VideoRepository videoRepository;
    private final HospitalService hospitalService;
    private final AdosRepository adosRepository;

    @Override
    @Transactional(readOnly = true)
    public ExamSummaryDTO getExamSummaryForChild(UUID childId) {
        // 1. 병원 연동 여부 확인
        boolean hasLinkedHospital = hospitalService.hasLinkedHospital(childId);
        if (!hasLinkedHospital) {
            return ExamSummaryDTO.empty(); // NEED_HOSPITAL
        }

        // 2. 가장 최신 검사 기록 조회
        Optional<Exam> latestExamOpt = examRepository.findFirstByChild_ChildIdOrderByCreatedAtDesc(childId);

        // 3. 검사 기록이 없으면 AVAILABLE 상태
        if (latestExamOpt.isEmpty()) {
            return new ExamSummaryDTO(
                    ChildHomeStatus.AVAILABLE,
                    0,
                    null,
                    null,
                    null
            );
        }

        Exam latestExam = latestExamOpt.get();

        // 4. 상태 계산
        ChildHomeStatus status = calculateExamStatus(latestExam);

        // 5. 업로드된 비디오 개수 계산
        int examProgress = (latestExam.getExamStatus() == ExamStatus.IN_PROGRESS)
                ? countUploadedVideos(latestExam)
                : 0;

        // 6. DTO 조립
        return new ExamSummaryDTO(
                status,
                examProgress,
                latestExam.getExamStartedAt() != null ? latestExam.getExamStartedAt().toLocalDate() : null,
                latestExam.getNextEligibleAt() != null ? latestExam.getNextEligibleAt().toLocalDate() : null,
                latestExam.getDraftExpiresAt()
        );
    }

    @Override
    @Transactional
    public ExamStartResponse createExam(Child child) {
        UUID childId = child.getChildId();

        // 1. 현재 검사 상태 확인
        ExamSummaryDTO examSummary = getExamSummaryForChild(childId);
        ChildHomeStatus currentStatus = examSummary.childHomeStatus();

        // ⭐ 디버깅 로그 추가
        log.info("검사 시작 시도 - childId: {}, currentStatus: {}, examSummary: {}",
                childId, currentStatus, examSummary);

        // 2. 검사 시작 가능 상태인지 확인 (AVAILABLE 또는 AVAILABLE_EXPIRED만 허용)
        if (!(currentStatus == ChildHomeStatus.AVAILABLE
                || currentStatus == ChildHomeStatus.AVAILABLE_EXPIRED)) {
            throw new ExamNotEligibleException();
        }

        // 3. AVAILABLE_EXPIRED인 경우, 기존 IN_PROGRESS 검사를 삭제 (만료된 데이터 정리)
        if (currentStatus == ChildHomeStatus.AVAILABLE_EXPIRED) {
            examRepository.findFirstByChild_ChildIdOrderByCreatedAtDesc(childId)
                    .ifPresent(examRepository::delete);
        }

        // 4. 새로운 Exam 엔티티 생성
        Exam newExam = Exam.builder()
                .child(child)
                .examStatus(ExamStatus.IN_PROGRESS)
                .submitted(false)
                .examStartedAt(null)  // 첫 비디오 업로드 시 설정됨
                .nextEligibleAt(null) // 검사 완료 시 설정됨
                .draftExpiresAt(LocalDateTime.now().plusDays(3)) // 검사 시작하면 설정!!
                .completedAt(null)
                .build();

        Exam savedExam = examRepository.save(newExam);

        log.info("새로운 검사 생성 - examId: {}, childId: {}",
                savedExam.getExamId(), childId);

        return ExamStartResponse.of(
                savedExam.getExamId(),
                childId,
                savedExam.getExamStatus()
        );
    }

    @Override
    @Transactional(readOnly = true)
    public Map<UUID, Exam> getLatestExamsByChildIds(List<UUID> childIds) {
        if (childIds == null || childIds.isEmpty()) {
            return Map.of();
        }

        // 각 아이별 최신 검사 조회
        return childIds.stream()
                .map(examRepository::findFirstByChild_ChildIdOrderByCreatedAtDesc)
                .filter(Optional::isPresent)
                .map(Optional::get)
                .collect(Collectors.toMap(
                        exam -> exam.getChild().getChildId(),
                        exam -> exam,
                        (existing, replacement) -> existing // 중복 시 기존 값 유지
                ));
    }

    /**
     * 검사 상태를 계산하는 핵심 로직
     */
    private ChildHomeStatus calculateExamStatus(Exam exam) {
        LocalDateTime now = LocalDateTime.now();
        ExamStatus examStatus = exam.getExamStatus();
        LocalDateTime draftExpiresAt = exam.getDraftExpiresAt();
        LocalDateTime nextEligibleAt = exam.getNextEligibleAt();

        // Case 1: 검사 완료 상태
        if (examStatus == ExamStatus.COMPLETED) {
            if (nextEligibleAt == null || !now.isBefore(nextEligibleAt)) {
                return ChildHomeStatus.AVAILABLE;
            }
            return ChildHomeStatus.COOLDOWN;
        }

        // Case 2: 검사 진행 중 상태 (IN_PROGRESS)
        if (examStatus == ExamStatus.IN_PROGRESS) {
            // ✅ 수정: draftExpiresAt이 null이면 검사 생성 직후
            if (draftExpiresAt == null) {
                return ChildHomeStatus.IN_PROGRESS;  // ✅ 변경
            }

            // draftExpiresAt이 지났으면 만료
            if (now.isAfter(draftExpiresAt)) {
                return ChildHomeStatus.AVAILABLE_EXPIRED;
            }

            // 진행 중
            return ChildHomeStatus.IN_PROGRESS;
        }

        return ChildHomeStatus.AVAILABLE;
    }

    /**
     * 업로드 완료된 비디오 개수 카운트 (UPLOADED 상태만)
     */
    private int countUploadedVideos(Exam exam) {
        List<Video> videos = videoRepository.findByExam(exam);
        return (int) videos.stream()
                .filter(v -> v.getVideoStatus() == VideoStatus.UPLOADED)
                .count();
    }

    @Override
    @Transactional(readOnly = true)
    public ExamInfoResponse getExamInfo(UUID childId, boolean underEighteen) {
        // 1. 가장 최신 검사 조회
        Exam latestExam = examRepository.findFirstByChild_ChildIdOrderByCreatedAtDesc(childId)
                .orElseThrow(ExamNotFoundException::new);

        // 2. 해당 검사의 모든 비디오 조회
        List<Video> videos = videoRepository.findByExamExamId(latestExam.getExamId());

        // 3. VideoType별로 매핑
        List<ExamInfoResponse.VideoTaskInfo> videoTasks = new ArrayList<>();

        addVideoTaskInfo(videoTasks, VideoType.POSE_IMITATION, videos);
        addVideoTaskInfo(videoTasks, VideoType.SPEECH_IMITATION, videos);
        addVideoTaskInfo(videoTasks, VideoType.NAME_FACING, videos);
        addVideoTaskInfo(videoTasks, VideoType.NAME_NON_FACING, videos);

        // 5. 응답 생성
        return ExamInfoResponse.builder()
                .examId(latestExam.getExamId().toString())
                .underEighteen(underEighteen)
                .status(latestExam.getExamStatus())
                .videoTasks(videoTasks)
                .build();
    }

    @Override
    @Transactional(readOnly = true)
    public List<Exam> getExamsByChildIds(List<UUID> childIds) {
        return examRepository.findByChild_ChildIdInOrderByCompletedAtDesc(childIds);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Exam> getExamsByChildId(UUID childId) {
        return examRepository.findByChild_ChildIdOrderByCompletedAtDesc(childId);
    }

    @Override
    @Transactional(readOnly = true)
    public AdosReportGraphsResponse getAdosGraphData(UUID childId) {
// 1. ADOS 히스토리 조회 (완료된 검사 기준, 날짜 오름차순)
        List<Ados> adosList = adosRepository.findAdosHistoryByChildId(childId);

        // 2. 시계열 데이터 리스트 초기화
        List<String> xAxis = new ArrayList<>();
        List<Integer> b6List = new ArrayList<>(), a8List = new ArrayList<>(), b18List = new ArrayList<>();
        List<Integer> a3List = new ArrayList<>();
        List<Integer> b1List = new ArrayList<>(), b4List = new ArrayList<>();
        List<Integer> b7List = new ArrayList<>();

        // 3. 엔티티 데이터 파싱
        for (Ados ados : adosList) {
            xAxis.add(ados.getExam().getCompletedAt().toLocalDate().toString());

            // 각 그래프에 필요한 항목 추출
            b6List.add(ados.getB6());
            a8List.add(ados.getA8());
            b18List.add(ados.getB18());
            a3List.add(ados.getA3());
            b1List.add(ados.getB1());
            b4List.add(ados.getB4());
            b7List.add(ados.getB7());
        }

        // 4. 그래프별 시리즈 구성
        var g1 = new AdosReportGraphsResponse.GraphSeries(Map.of("b6", b6List, "a8", a8List, "b18", b18List));
        var g2 = new AdosReportGraphsResponse.GraphSeries(Map.of("a3", a3List, "b18", b18List));
        var g3 = new AdosReportGraphsResponse.GraphSeries(Map.of("b1", b1List, "b4", b4List, "b6", b6List, "b18", b18List));
        var g4 = new AdosReportGraphsResponse.GraphSeries(Map.of("b7", b7List, "b18", b18List));

        return new AdosReportGraphsResponse(xAxis, new AdosReportGraphsResponse.GraphGroups(g1, g2, g3, g4));
    }

    @Override
    @Transactional(readOnly = true)
    public AdosDetailResponse getAdosDetail(UUID examId) {
        Ados ados = adosRepository.findByExamExamId(examId)
                .orElseThrow(() -> new IllegalArgumentException("해당 검사의 ADOS 기록이 존재하지 않습니다."));

        Exam exam = ados.getExam();
        Child child = exam.getChild();

        // 1. 개월수 계산 (AdosCalculationServiceImpl과 동일한 방식 권장)
        long ageMonths = 0;
        if (child.getBirthdate() != null) {
            java.time.Period period = java.time.Period.between(child.getBirthdate(), java.time.LocalDate.now());
            ageMonths = period.getYears() * 12L + period.getMonths();
        }

        AdosDetailResponse.AdosScoresDTO scoresDto;

        // 2. 연령 그룹별 필드 매핑
        if (ageMonths < 21) {
            // [21개월 미만] 관련 항목은 null이면 0으로, 관련 없는 항목은 null 유지(응답에서 제외)
            scoresDto = new AdosDetailResponse.AdosScoresDTO(
                    nz(ados.getA2()), nz(ados.getA3()), null, nz(ados.getA8()),           // A
                    nz(ados.getB1()), nz(ados.getB4()), nz(ados.getB5()), nz(ados.getB6()), // B
                    null, null, null, nz(ados.getB12()), nz(ados.getB13()),              // B
                    nz(ados.getB14()), nz(ados.getB15()), null, null,                    // B
                    nz(ados.getSocialAffectTotal()),                                     // SA Total
                    nz(ados.getD1()), nz(ados.getD2()), nz(ados.getD5()),                // D
                    nz(ados.getRrbTotal()),                                              // RRB Total
                    nz(ados.getTotal())                                                   // Total
            );
        } else {
            // [21개월 이상] 관련 항목은 null이면 0으로, 관련 없는 항목은 null 유지(응답에서 제외)
            scoresDto = new AdosDetailResponse.AdosScoresDTO(
                    null, null, nz(ados.getA7()), null,                                  // A
                    nz(ados.getB1()), nz(ados.getB4()), nz(ados.getB5()), null,            // B
                    nz(ados.getB7()), nz(ados.getB8()), nz(ados.getB9()), null,            // B
                    nz(ados.getB13()), null, nz(ados.getB15()), nz(ados.getB16b()),        // B
                    nz(ados.getB18()),                                                   // B
                    nz(ados.getSocialAffectTotal()),                                     // SA Total
                    nz(ados.getD1()), nz(ados.getD2()), nz(ados.getD5()),                // D
                    nz(ados.getRrbTotal()),                                              // RRB Total
                    nz(ados.getTotal())                                                   // Total
            );
        }

        return new AdosDetailResponse(ados.getAdosId(), examId, scoresDto);
    }

    /**
     * Null-to-Zero Helper
     */
    private Integer nz(Integer val) {
        return val == null ? 0 : val;
    }

    @Override
    @Transactional(readOnly = true)
    public Exam getExamById(UUID examId) {
        return examRepository.findById(examId)
                .orElseThrow(ExamNotFoundException::new);
    }

    private void addVideoTaskInfo(List<ExamInfoResponse.VideoTaskInfo> videoTasks,
                                  VideoType videoType,
                                  List<Video> videos) {
        Video video = videos.stream()
                .filter(v -> v.getVideoType() == videoType)
                .findFirst()
                .orElse(null);

        if (video != null && video.getVideoStatus() == VideoStatus.UPLOADED) {
            videoTasks.add(ExamInfoResponse.VideoTaskInfo.builder()
                    .videoType(videoType.name())  // VideoType enum 이름 그대로 사용
                    .status("UPLOADED")
                    .videoId(video.getVideoId().toString())
                    .build());
        } else {
            videoTasks.add(ExamInfoResponse.VideoTaskInfo.builder()
                    .videoType(videoType.name())  // VideoType enum 이름 그대로 사용
                    .status("EMPTY")
                    .videoId(null)
                    .build());
        }
    }
}
