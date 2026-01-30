package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.request.CalendarRequest;
import com.ssafy.aitime.domain.hospital.dto.request.ReservationCreateRequest;
import com.ssafy.aitime.domain.hospital.dto.response.CalendarReservationResponse;
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
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReservationServiceImpl implements ReservationService {

    private final ReservationRepository reservationRepository;
    private final HospitalChildrenRepository hospitalChildrenRepository;
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
    public List<LocalDate> getHospitalReservationDates(UUID hospitalId, YearMonth yearMonth) {
        // 1. 해당 월의 시작과 끝 계산
        LocalDate firstDayOfMonth = yearMonth.atDay(1);
        LocalDateTime startOfMonth = firstDayOfMonth.atStartOfDay();
        LocalDateTime endOfMonth = yearMonth.plusMonths(1).atDay(1).atStartOfDay();

        // 2. 해당 병원의 해당 월 예약 조회
        List<Reservation> reservations = reservationRepository
                .findReservationsByHospitalAndMonth(hospitalId, startOfMonth, endOfMonth);

        // 3. scheduledAt에서 날짜만 추출하고 중복 제거
        return reservations.stream()
                .map(r -> r.getScheduledAt().toLocalDate())
                .distinct()
                .sorted()
                .toList();
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
