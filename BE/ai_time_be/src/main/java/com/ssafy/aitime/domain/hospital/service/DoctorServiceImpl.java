package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.ChildResponse;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.exception.DoctorNotFoundException;
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

@Slf4j
@Service
@RequiredArgsConstructor
public class DoctorServiceImpl implements DoctorService{

    private final ReservationRepository reservationRepository;
    private final HospitalChildrenRepository hospitalChildrenRepository;
    private final HospitalStaffRepository hospitalStaffRepository;
    private final ChildRepository childRepository;
    private final ExamRepository examRepository;

    private void validateDoctorId(UUID doctorId) {
        log.debug("의사 ID 유효성 검증 시작: {}", doctorId);

        boolean exists = hospitalStaffRepository
                .existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                        doctorId, StaffRole.DOCTOR, RecordStatus.ACTIVE
                );

        if (!exists) {
            throw new DoctorNotFoundException(
                    String.format("존재하지 않거나 활성화되지 않은 의사입니다. (ID: %s)", doctorId)
            );
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
        List<Exam> exams = examRepository.findByChild_ChildIdInOrderByCompletedAtDesc(childIds);

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
}
