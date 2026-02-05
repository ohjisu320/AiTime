package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.dto.response.ExamWithVideosResponse;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.service.ExamService;
import com.ssafy.aitime.domain.exam.service.VideoService;
import com.ssafy.aitime.domain.exam.service.dto.VideoSummary;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.ChildResponse;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
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
    private final ChildRepository childRepository;

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
        // TODO 0: 의사 ID 유효성 검증
        validateDoctorId(doctorId);  // ← 추가!

        log.info("환자 검색 시작 - 의사 ID: {}, 검색 조건: {}", doctorId, patientSearchRequest);

        // TODO 1: 날짜 필터링하여 Reservation 조회
        LocalDate filterDate = patientSearchRequest.getEffectiveDate();
        List<UUID> hospitalChildrenIds;

        if (filterDate != null) {
            // 특정 날짜의 예약만 조회
            LocalDateTime startOfDay = filterDate.atStartOfDay();
            LocalDateTime endOfDay = filterDate.plusDays(1).atStartOfDay();

            hospitalChildrenIds = reservationRepository
                    .findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                            doctorId,
                            ReservationStatus.CANCELLED,
                            startOfDay,
                            endOfDay
                    )
                    .stream()
                    .map(r -> r.getHospitalChildren().getHospitalChildrenId())
                    .distinct()
                    .toList();
        } else {
            // 날짜 필터 없음 - 전체 예약 조회
            hospitalChildrenIds = reservationRepository
                    .findByDoctorIdAndReservationStatusNot(
                            doctorId,
                            ReservationStatus.CANCELLED
                    )
                    .stream()
                    .map(r -> r.getHospitalChildren().getHospitalChildrenId())
                    .distinct()
                    .toList();
        }

        // 예약이 없으면 빈 결과 반환
        if (hospitalChildrenIds.isEmpty()) {
            return new PatientSearchResponse(Collections.emptyList(), 0);
        }

        // TODO 2: hospitalChildrenIds를 이용하여 hospital_children 테이블에서 child_id UUID 뽑기
        List<UUID> childIds = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(hospitalChildrenIds, LinkStatus.ACTIVE)
                .stream()
                .map(hc -> hc.getChild().getChildId())
                .distinct()
                .toList();

        // TODO 3: childIds를 이용하여 child 테이블에서 객체 받아오기
        List<Child> children = childRepository.findByChildIdInAndRecordStatus(childIds, RecordStatus.ACTIVE);

        // TODO 4: childIds로 exam 다 가져오기
        List<Exam> exams = examService.getExamsByChildIds(childIds);

        // TODO 5: childId별 최신 ExamStatus 매핑
        Map<UUID, String> latestExamStatusByChildId = new HashMap<>();

        for (Exam exam : exams) {
            UUID childId = exam.getChild().getChildId();

            // 이미 있으면 스킵 (createdAt desc라서 처음이 최신)
            latestExamStatusByChildId.putIfAbsent(childId, exam.getExamStatus().name());
        }

        // TODO 6: DTO 변환
        List<ChildResponse> responses = new ArrayList<>();

        for (Child child : children) {
            UUID childId = child.getChildId();

            String latestExamStatus = latestExamStatusByChildId.getOrDefault(childId, "NONE");

            int monthlyAge = calcMonthlyAge(child.getBirthdate());

            responses.add(new ChildResponse(
                    childId,
                    child.getUser().getUserId(),
                    child.getName(),
                    monthlyAge,
                    child.getBirthdate(),
                    child.getGender().name(),
                    latestExamStatus
            ));
        }

        // TODO 7: 이름 필터링 (메모리)
        if (patientSearchRequest.hasNameFilter()) {
            String nameFilter = patientSearchRequest.name().toLowerCase();
            responses = responses.stream()
                    .filter(r -> r.name().toLowerCase().contains(nameFilter))
                    .toList();
        }

        // TODO 8: 결과 상태 필터링 (메모리
        if (patientSearchRequest.hasResultStatusFilter()) {
            String statusFilter = patientSearchRequest.resultStatus().toUpperCase();
            responses = responses.stream()
                    .filter(r -> r.latestExamStatus().equals(statusFilter))
                    .toList();
        }

        // 전체 결과 개수 저장 (페이징 전)
        int totalCount = responses.size();

        // TODO 9: 페이징 처리
        int page = patientSearchRequest.page();
        int size = patientSearchRequest.size();
        int fromIndex = page * size;
        int toIndex = Math.min(fromIndex + size, responses.size());

        List<ChildResponse> pagedResponses;
        if (fromIndex < responses.size()) {
            pagedResponses = responses.subList(fromIndex, toIndex);
        } else {
            pagedResponses = Collections.emptyList();
        }

        // TODO 10: 최종 결과 반환
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
