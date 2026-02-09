package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.child.service.ChildService;
import com.ssafy.aitime.domain.exam.dto.response.AdosDetailResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamWithVideosResponse;
import com.ssafy.aitime.domain.exam.entity.Ados;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.service.ExamService;
import com.ssafy.aitime.domain.exam.service.VideoService;
import com.ssafy.aitime.domain.exam.service.dto.VideoSummary;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.*;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.exception.DoctorNotFoundException;
import com.ssafy.aitime.domain.hospital.exception.HospitalChildrenNotFoundException;
import com.ssafy.aitime.domain.hospital.exception.HospitalStaffAccessDeniedException;
import com.ssafy.aitime.domain.hospital.exception.HospitalStaffNotFoundException;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import com.ssafy.aitime.domain.hospital.repository.HospitalStaffRepository;
import com.ssafy.aitime.domain.hospital.repository.ReservationRepository;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class DoctorServiceImpl implements DoctorService{

    private final ReservationRepository reservationRepository;
    private final HospitalChildrenRepository hospitalChildrenRepository;
    private final HospitalStaffRepository hospitalStaffRepository;
    private final ChildService childService;

    private final ExamService examService;
    private final VideoService videoService;

    private void validateDoctorId(UUID doctorId) {
        log.debug("의사 ID 유효성 검증 시작: {}", doctorId);

        boolean exists = hospitalStaffRepository
                .existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                        doctorId, StaffRole.DOCTOR, RecordStatus.ACTIVE
                );

        if (!exists) {
            throw new DoctorNotFoundException();
        }
    }

    private int calcMonthlyAge(LocalDate birthdate) {
        return (int) ChronoUnit.MONTHS.between(birthdate, LocalDate.now());
    }

    @Transactional(readOnly = true)
    @Override
    public PatientSearchResponse getSearchPatientList(
            UUID doctorId,
            PatientSearchRequest patientSearchRequest
    ) {
        validateDoctorId(doctorId);

        log.info("환자 검색 시작 - 의사 ID: {}, 검색 조건: {}", doctorId, patientSearchRequest);

        // 1. 날짜 필터링하여 Reservation 조회
        LocalDate filterDate = patientSearchRequest.getEffectiveDate();
        List<Reservation> reservations;

        if (filterDate != null) {
            LocalDateTime startOfDay = filterDate.atStartOfDay();
            LocalDateTime endOfDay = filterDate.plusDays(1).atStartOfDay();

            reservations = reservationRepository
                    .findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                            doctorId,
                            ReservationStatus.CANCELLED,
                            startOfDay,
                            endOfDay
                    );
        } else {
            reservations = reservationRepository
                    .findByDoctorIdAndReservationStatusNot(
                            doctorId,
                            ReservationStatus.CANCELLED
                    );
        }

        if (reservations.isEmpty()) {
            return new PatientSearchResponse(Collections.emptyList(), 0);
        }

        // 2. HospitalChildren ID별로 최신 예약 매핑 (scheduledAt 정보 필요)
        Map<UUID, Reservation> latestReservationByHospitalChildrenId = new HashMap<>();
        for (Reservation reservation : reservations) {
            UUID hospitalChildrenId = reservation.getHospitalChildren().getHospitalChildrenId();
            latestReservationByHospitalChildrenId.merge(
                    hospitalChildrenId,
                    reservation,
                    (existing, current) ->
                            current.getScheduledAt().isAfter(existing.getScheduledAt()) ? current : existing
            );
        }

        // 3. HospitalChildren 조회
        List<UUID> hospitalChildrenIds = new ArrayList<>(latestReservationByHospitalChildrenId.keySet());
        List<HospitalChildren> hospitalChildrenList = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(hospitalChildrenIds, LinkStatus.ACTIVE);

        // 4. Child ID 추출 및 Child 조회
        List<UUID> childIds = hospitalChildrenList.stream()
                .map(hc -> hc.getChild().getChildId())
                .distinct()
                .toList();

        Map<UUID, Child> childMap = childService.getChildrenByIds(childIds)  // ← 수정
                .stream()
                .collect(Collectors.toMap(Child::getChildId, child -> child));

        // 5. childId별 최신 Exam 조회
        List<Exam> exams = examService.getExamsByChildIds(childIds);

        Map<UUID, Exam> latestExamByChildId = new HashMap<>();
        for (Exam exam : exams) {
            UUID childId = exam.getChild().getChildId();
            // getExamsByChildIds가 createdAt desc로 정렬되어 있다고 가정
            // 첫 번째로 나온 것이 최신이므로 putIfAbsent 사용
            latestExamByChildId.putIfAbsent(childId, exam);
        }

        // 6. DTO 변환
        List<ChildResponse> responses = new ArrayList<>();

        for (HospitalChildren hospitalChildren : hospitalChildrenList) {
            UUID hospitalChildrenId = hospitalChildren.getHospitalChildrenId();
            Child child = childMap.get(hospitalChildren.getChild().getChildId());

            if (child == null) continue;

            Reservation reservation = latestReservationByHospitalChildrenId.get(hospitalChildrenId);
            Exam latestExam = latestExamByChildId.get(child.getChildId());

            String examStatus = latestExam != null ? latestExam.getExamStatus().name() : "NONE";
            boolean isSubmitted = latestExam != null && latestExam.isSubmitted();

            int months = calcMonthlyAge(child.getBirthdate());

            responses.add(new ChildResponse(
                    hospitalChildrenId,
                    child.getName(),
                    child.getGender().name(),
                    months,
                    reservation.getScheduledAt(),
                    examStatus,
                    isSubmitted
            ));
        }

        // 7. 이름 필터링
        if (patientSearchRequest.hasNameFilter()) {
            String nameFilter = patientSearchRequest.name().toLowerCase();
            responses = responses.stream()
                    .filter(r -> r.childName().toLowerCase().contains(nameFilter))
                    .toList();
        }

        // 8. 결과 상태 필터링
        if (patientSearchRequest.hasResultStatusFilter()) {
            String statusFilter = patientSearchRequest.resultStatus().toUpperCase();
            responses = responses.stream()
                    .filter(r -> r.examStatus().equals(statusFilter))
                    .toList();
        }

        int totalCount = responses.size();

        // 9. 페이징 처리
        int page = patientSearchRequest.page();
        int size = patientSearchRequest.size();
        int fromIndex = page * size;
        int toIndex = Math.min(fromIndex + size, responses.size());

        List<ChildResponse> pagedResponses = fromIndex < responses.size()
                ? responses.subList(fromIndex, toIndex)
                : Collections.emptyList();

        return new PatientSearchResponse(pagedResponses, totalCount);
    }

    /**
     * 특정 환아의 검사 목록 조회 (비디오 목록 포함)
     */
    @Override
    @Transactional(readOnly = true)
    public List<ExamWithVideosResponse> getExamsByHospitalChildren(UUID hospitalStaffId, UUID hospitalChildrenId) {
        log.info("환아별 검사 목록 조회 시작 - staffId: {}, hospitalChildrenId: {}",
                hospitalStaffId, hospitalChildrenId);

        // 1. HospitalStaff 조회
        HospitalStaff staff = hospitalStaffRepository.findById(hospitalStaffId)
                .orElseThrow(() -> new HospitalStaffNotFoundException());

        // 2. HospitalChildren 조회
        HospitalChildren hospitalChildren = hospitalChildrenRepository.findById(hospitalChildrenId)
                .orElseThrow(() -> new HospitalChildrenNotFoundException());

        // 3. 권한 검증
        if (!hospitalChildren.getHospital().getHospitalId().equals(staff.getHospital().getHospitalId())) {
            log.warn("권한 없는 접근 시도 - staffId: {}, staffHospitalId: {}, targetHospitalId: {}",
                    hospitalStaffId,
                    staff.getHospital().getHospitalId(),
                    hospitalChildren.getHospital().getHospitalId());
            throw new HospitalStaffAccessDeniedException();
        }

        // 4. LinkStatus 확인
        if (hospitalChildren.getLinkStatus() != LinkStatus.ACTIVE) {
            log.warn("비활성화된 환아 접근 시도 - hospitalChildrenId: {}, status: {}",
                    hospitalChildrenId, hospitalChildren.getLinkStatus());
            return Collections.emptyList();
        }

        // 5. Child의 모든 Exam 조회 (✅ ExamService 사용)
        UUID childId = hospitalChildren.getChild().getChildId();
        List<Exam> exams = examService.getExamsByChildId(childId);

        if (exams.isEmpty()) {
            log.info("검사 내역 없음 - childId: {}", childId);
            return Collections.emptyList();
        }

        // 6. 각 Exam의 Video 목록 조회 (✅ VideoService 사용)
        List<UUID> examIds = exams.stream()
                .map(Exam::getExamId)
                .collect(Collectors.toList());

        List<Video> videos = videoService.getVideosByExamIds(examIds);

        // ExamId별로 Video 그룹화
        Map<UUID, List<Video>> videosByExamId = videos.stream()
                .collect(Collectors.groupingBy(v -> v.getExam().getExamId()));

        // 7. DTO 변환
        List<ExamWithVideosResponse> responses = new ArrayList<>();
        for (Exam exam : exams) {
            List<Video> examVideos = videosByExamId.getOrDefault(exam.getExamId(), Collections.emptyList());

            List<VideoSummary> videoSummaries = examVideos.stream()
                    .map(v -> VideoSummary.builder()
                            .videoId(v.getVideoId().toString())
                            .videoType(v.getVideoType().name())
                            .build())
                    .collect(Collectors.toList());

            LocalDate examDate = getExamDate(exam);

            responses.add(ExamWithVideosResponse.builder()
                    .examId(exam.getExamId().toString())
                    .examDate(examDate)
                    .examStatus(exam.getExamStatus().name())
                    .videos(videoSummaries)
                    .build());
        }

        log.info("환아별 검사 목록 조회 완료 - childId: {}, examCount: {}", childId, responses.size());
        return responses;
    }

    @Override
    @Transactional(readOnly = true)
    public AdosReportGraphsResponse getAdosGraphData(UUID hospitalStaffId, UUID hospitalChildrenId) {
// 1. HospitalStaff 및 HospitalChildren 조회 및 권한 검증
        HospitalStaff staff = hospitalStaffRepository.findById(hospitalStaffId)
                .orElseThrow(HospitalStaffNotFoundException::new);
        HospitalChildren hospitalChildren = hospitalChildrenRepository.findById(hospitalChildrenId)
                .orElseThrow(HospitalChildrenNotFoundException::new);

        // 병원 ID 일치 확인
        if (!hospitalChildren.getHospital().getHospitalId().equals(staff.getHospital().getHospitalId())) {
            throw new HospitalStaffAccessDeniedException();
        }

        // 2. ExamService를 통해 타 도메인(ADOS) 데이터 조회
        UUID childId = hospitalChildren.getChild().getChildId();
        return examService.getAdosGraphData(childId);
    }

    @Override
    @Transactional(readOnly = true)
    public AdosDetailResponse getAdosDetail(UUID hospitalStaffId, UUID examId) {
// 1. 의사 및 검사 정보 조회
        HospitalStaff staff = hospitalStaffRepository.findById(hospitalStaffId)
                .orElseThrow(HospitalStaffNotFoundException::new);

        Exam exam = examService.getExamById(examId);

        // 2. 권한 검증: 검사 대상 환아가 의사와 같은 병원 소속인지 확인
        boolean hasAccess = hospitalChildrenRepository.existsByChildAndHospitalAndLinkStatus(
                exam.getChild(), staff.getHospital(), LinkStatus.ACTIVE);

        if (!hasAccess) {
            throw new HospitalStaffAccessDeniedException();
        }

        // 3. ExamService 호출
        return examService.getAdosDetail(examId);
    }

    @Override
    @Transactional(readOnly = true)
    public InitialReportResponse getInitialReport(UUID hospitalStaffId, UUID hospitalChildrenId, Long expiresInSec) {
// 1. 의사 정보 조회 및 권한 확인 (기존 로직 재활용)
        HospitalStaff staff = hospitalStaffRepository.findById(hospitalStaffId)
                .orElseThrow(HospitalStaffNotFoundException::new);
        HospitalChildren hospitalChildren = hospitalChildrenRepository.findById(hospitalChildrenId)
                .orElseThrow(HospitalChildrenNotFoundException::new);
        HospitalStaffPrincipal principal = HospitalStaffPrincipal.from(staff); // 권한 검증용 객체 생성

        // 2. 권한 검증
        if (!hospitalChildren.getHospital().getHospitalId().equals(staff.getHospital().getHospitalId())) {
            throw new HospitalStaffAccessDeniedException();
        }

        int expiresAt = (expiresInSec != null) ? expiresInSec.intValue() : 300;

        // 2. 환아별 검사 목록 조회 (기존 getExamsByHospitalChildren 재활용)
        List<ExamWithVideosResponse> examVideoList = getExamsByHospitalChildren(hospitalStaffId, hospitalChildrenId);

        // 검사 이력이 없는 경우 조기 반환
        if (examVideoList.isEmpty()) {
            return new InitialReportResponse(Collections.emptyList(), null, null, null);
        }

        // 3. 최신(Latest) 정보 추출 (첫 번째 요소가 최신)
        ExamWithVideosResponse latestExamInfo = examVideoList.get(0);
        UUID latestExamId = UUID.fromString(latestExamInfo.examId());

        // 4. 최신 ADOS 상세 조회 (기존 examService.getAdosDetail 재활용)
        AdosDetailResponse latestAdosDetail = null;
        try {
            latestAdosDetail = examService.getAdosDetail(latestExamId);
        } catch (Exception e) {
            log.warn("최신 ADOS 상세 정보가 없습니다. examId: {}", latestExamId);
        }

        // 5. ADOS 그래프 데이터 조회 (기존 getAdosGraphData 재활용)
        UUID childId = hospitalChildren.getChild().getChildId(); // childId 조회 필요
        AdosReportGraphsResponse adosGraphs = examService.getAdosGraphData(childId);

        // 6. 최신 POSE_IMITATION 비디오 상세 정보 구성
        LatestPoseVideoResponse latestPoseVideo = null;
        Optional<String> poseVideoId = latestExamInfo.videos().stream()
                .filter(v -> "POSE_IMITATION".equals(v.videoType()))
                .map(v -> v.videoId())
                .findFirst();

        if (poseVideoId.isPresent()) {
            latestPoseVideo = videoService.getLatestPoseVideoResponse(
                    principal,
                    latestExamId,
                    UUID.fromString(poseVideoId.get()),
                    expiresAt
            );
        }

        return new InitialReportResponse(
                examVideoList,
                latestPoseVideo,
                adosGraphs,
                latestAdosDetail
        );
    }

    private LocalDate getExamDate(Exam exam) {
        if (exam.getCompletedAt() != null) {
            return exam.getCompletedAt().toLocalDate();
        }
        if (exam.getExamStartedAt() != null) {
            return exam.getExamStartedAt().toLocalDate();
        }
        return exam.getCreatedAt().toLocalDate();
    }
}
