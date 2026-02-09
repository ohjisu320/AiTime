package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.service.ChildService;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.service.ExamService;
import com.ssafy.aitime.domain.hospital.dto.request.CalendarRequest;
import com.ssafy.aitime.domain.hospital.dto.request.ReservationCreateRequest;
import com.ssafy.aitime.domain.hospital.dto.response.CalendarReservationResponse;
import com.ssafy.aitime.domain.hospital.dto.response.ReservationListResponse;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.hospital.exception.DoctorNotFoundException;
import com.ssafy.aitime.domain.hospital.exception.HospitalChildrenNotFoundException;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import com.ssafy.aitime.domain.hospital.repository.ReservationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReservationServiceImpl implements ReservationService {

    private final ReservationRepository reservationRepository;
    private final HospitalChildrenRepository hospitalChildrenRepository;

    private final ChildService childService;
    private final ExamService examService;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    /**
     * 특정 의사의 년/월별 예약 날짜 조회
     */
    @Transactional(readOnly = true)
    @Override
    public CalendarReservationResponse getReservationDates(UUID doctorId, CalendarRequest calendarRequest) {
        log.info("Fetching reservation dates for doctor: {}, calendarRequest: {}",
                doctorId, calendarRequest);

        // 입력 유효성 검증
        validateInput(doctorId, calendarRequest);

        // 해당 월의 시작일과 종료일 계산
        YearMonth yearMonth = YearMonth.of(calendarRequest.year(), calendarRequest.month());
        LocalDateTime startOfMonth = yearMonth.atDay(1).atStartOfDay();
        LocalDateTime endOfMonth = yearMonth.atEndOfMonth().atTime(23, 59, 59);

        log.debug("Querying reservations between {} and {}", startOfMonth, endOfMonth);

        // Repository에서 기간으로 필터링된 예약 조회
        List<Reservation> reservations = reservationRepository
                .findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                        doctorId,
                        ReservationStatus.CANCELLED,
                        startOfMonth,
                        endOfMonth
                );

        // 날짜만 추출하여 포맷 변환 (중복 제거 및 정렬)
        List<String> dates = reservations.stream()
                .map(reservation -> reservation.getScheduledAt().toLocalDate()
                        .format(DATE_FORMATTER))
                .distinct()
                .sorted()
                .toList();

        log.info("Found {} reservation dates for doctor: {}", dates.size(), doctorId);

        return CalendarReservationResponse.of(dates);
    }

    @Transactional
    @Override
    public void insertReservation(ReservationCreateRequest request) {
        // 1. HospitalChildren 조회 (필수!)
        HospitalChildren hospitalChildren = hospitalChildrenRepository.findById(request.hospitalChildrenId())
                .orElseThrow(HospitalChildrenNotFoundException::new);

        // 2. Reservation 생성
        Reservation reservation = Reservation.builder()
                .hospitalChildren(hospitalChildren)  // 엔티티 객체 전달!
                .scheduledAt(request.scheduledAt())
                .doctorId(request.doctorId())
                // .reservationStatus는 기본값(SCHEDULED)으로 자동 설정됨
                .build();

        // 4. 저장
        reservationRepository.save(reservation);
    }

    @Override
    @Transactional(readOnly = true)
    public List<LocalDate> getHospitalReservationDates(UUID hospitalId, int year, int month) {
        // 1. 해당 월의 시작과 끝 계산
        LocalDate firstDayOfMonth = LocalDate.of(year, month, 1);
        LocalDateTime startOfMonth = firstDayOfMonth.atStartOfDay();
        LocalDateTime endOfMonth = firstDayOfMonth.plusMonths(1).atStartOfDay();

        // 2. 해당 병원의 해당 월 예약 조회
        List<Reservation> reservations = reservationRepository
                .findReservationsByHospitalAndMonth(hospitalId, startOfMonth, endOfMonth);

        // 3. scheduledAt에서 날짜만 추출하고 중복 제거 + 정렬
        return reservations.stream()
                .map(r -> r.getScheduledAt().toLocalDate())
                .distinct()
                .sorted()
                .toList();
    }


    @Override
    @Transactional(readOnly = true)
    public List<ReservationListResponse> getReservationList(UUID hospitalId, LocalDate date) {
        log.info("Fetching reservation list for hospital: {}, date: {}", hospitalId, date);

        // 1. 날짜 범위 계산
        LocalDateTime startOfDay = date.atStartOfDay();
        LocalDateTime endOfDay = date.plusDays(1).atStartOfDay();

        // 2. 해당 병원의 해당 날짜 예약 조회
        List<Reservation> reservations = reservationRepository
                .findReservationsByHospitalAndDate(hospitalId, startOfDay, endOfDay);

        // 3. 예약이 없으면 빈 리스트 반환
        if (reservations.isEmpty()) {
            log.info("No reservations found for hospital: {}, date: {}", hospitalId, date);
            return List.of();
        }

        // 4. 아이 ID 목록 추출
        List<UUID> childIds = reservations.stream()
                .map(r -> r.getHospitalChildren().getChild().getChildId())
                .distinct()
                .toList();

        log.debug("Found {} unique children in reservations", childIds.size());

        // 5. Child 도메인 서비스를 통해 아이 정보 조회
        List<Child> children = childService.getChildrenByIds(childIds);
        Map<UUID, Child> childMap = children.stream()
                .collect(Collectors.toMap(Child::getChildId, child -> child));

        // 6. Exam 도메인 서비스를 통해 최신 검사 정보 조회
        Map<UUID, Exam> examMap = examService.getLatestExamsByChildIds(childIds);

        // 7. DTO 변환
        List<ReservationListResponse> responses = reservations.stream()
                .map(reservation -> {
                    HospitalChildren hc = reservation.getHospitalChildren();
                    UUID childId = hc.getChild().getChildId();
                    Child child = childMap.get(childId);
                    Exam exam = examMap.get(childId);

                    return ReservationListResponse.of(
                            hc.getHospitalChildrenId(),
                            child,
                            exam
                    );
                })
                .toList();

        log.info("Successfully created {} reservation responses", responses.size());

        return responses;
    }

    /**
     * 입력값 유효성 검증
     */
    private void validateInput(UUID doctorId, CalendarRequest calendarRequest) {
        // 1️⃣ null 체크를 먼저! (NPE 방지)
        if (doctorId == null) {
            throw new DoctorNotFoundException();
        }
    }
}
