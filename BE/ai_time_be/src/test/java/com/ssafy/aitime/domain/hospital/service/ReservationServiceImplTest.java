package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.request.CalendarRequest;
import com.ssafy.aitime.domain.hospital.dto.response.CalendarReservationResponse;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.hospital.exception.DoctorNotFoundException;
import com.ssafy.aitime.domain.hospital.repository.ReservationRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

/**
 * ReservationService 테스트
 */
@ExtendWith(MockitoExtension.class)
@AutoConfigureMockMvc(addFilters = false)
@DisplayName("ReservationService 테스트")
class ReservationServiceImplTest {

    @Mock
    private ReservationRepository reservationRepository;

    @InjectMocks
    private ReservationServiceImpl reservationService;

    private static final UUID TEST_DOCTOR_ID = UUID.fromString("550e8400-e29b-41d4-a716-446655440000");

    @Nested
    @DisplayName("getReservationDates - 성공 케이스")
    class getReservationDatesSuccessCases {

        @Test
        @DisplayName("예약이 있는 날짜 조회 성공")
        void getReservationDates_WithReservations_Success() {
            // given
            CalendarRequest request = new CalendarRequest(2026, 1);
            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 1, 5, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 5, 14, 0)), // 같은 날 중복
                    createReservation(LocalDateTime.of(2026, 1, 19, 9, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 20, 15, 0))
            );

            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    eq(TEST_DOCTOR_ID),
                    eq(ReservationStatus.CANCELLED),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(mockReservations);

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response).isNotNull();
            assertThat(response.data()).hasSize(3); // 중복 제거됨
            assertThat(response.data()).containsExactly("2026-01-05", "2026-01-19", "2026-01-20");

            verify(reservationRepository).findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    eq(TEST_DOCTOR_ID),
                    eq(ReservationStatus.CANCELLED),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            );
        }

        @Test
        @DisplayName("예약이 없는 경우 빈 리스트 반환")
        void getReservationDates_NoReservations_ReturnsEmptyList() {
            // given
            CalendarRequest request = new CalendarRequest(2026, 2);
            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    eq(TEST_DOCTOR_ID),
                    eq(ReservationStatus.CANCELLED),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(Collections.emptyList());

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response).isNotNull();
            assertThat(response.data()).isEmpty();
        }

        @Test
        @DisplayName("같은 날짜의 여러 예약이 중복 제거되어 반환")
        void getReservationDates_SameDateMultipleReservations_Deduplicated() {
            // given
            CalendarRequest request = new CalendarRequest(2026, 1);
            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 1, 15, 9, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 15, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 15, 14, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 15, 16, 0))
            );

            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    any(UUID.class),
                    any(ReservationStatus.class),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(mockReservations);

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response.data()).hasSize(1);
            assertThat(response.data()).containsExactly("2026-01-15");
        }

        @Test
        @DisplayName("날짜가 오름차순으로 정렬되어 반환")
        void getReservationDates_ReturnsSorted() {
            // given
            CalendarRequest request = new CalendarRequest(2026, 1);
            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 1, 25, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 5, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 15, 10, 0))
            );

            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    any(UUID.class),
                    any(ReservationStatus.class),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(mockReservations);

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response.data()).containsExactly("2026-01-05", "2026-01-15", "2026-01-25");
        }

        @Test
        @DisplayName("12월 조회 성공")
        void getReservationDates_December_Success() {
            // given
            CalendarRequest request = new CalendarRequest(2026, 12);
            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 12, 24, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 12, 25, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 12, 31, 10, 0))
            );

            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    any(UUID.class),
                    any(ReservationStatus.class),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(mockReservations);

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response.data()).hasSize(3);
            assertThat(response.data()).containsExactly("2026-12-24", "2026-12-25", "2026-12-31");
        }

        @Test
        @DisplayName("2월(28일) 조회 성공")
        void getReservationDates_February_Success() {
            // given
            CalendarRequest request = new CalendarRequest(2026, 2);
            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 2, 1, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 2, 14, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 2, 28, 10, 0))
            );

            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    any(UUID.class),
                    any(ReservationStatus.class),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(mockReservations);

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response.data()).hasSize(3);
            assertThat(response.data()).contains("2026-02-01", "2026-02-14", "2026-02-28");
        }

        @Test
        @DisplayName("윤년 2월(29일) 조회 성공")
        void getReservationDates_LeapYearFebruary_Success() {
            // given
            CalendarRequest request = new CalendarRequest(2024, 2); // 2024는 윤년
            List<Reservation> mockReservations = List.of(
                    createReservation(LocalDateTime.of(2024, 2, 29, 10, 0))
            );

            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    any(UUID.class),
                    any(ReservationStatus.class),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(mockReservations);

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response.data()).containsExactly("2024-02-29");
        }
    }

    @Nested
    @DisplayName("getReservationDates - 실패 케이스")
    class getReservationDatesFailureCases {

        @Test
        @DisplayName("doctorId가 null인 경우 DoctorNotFoundException 발생")
        void getReservationDates_NullDoctorId_ThrowsException() {
            // given
            CalendarRequest request = new CalendarRequest(2026, 1);

            // when & then
            assertThatThrownBy(() -> reservationService.getReservationDates(null, request))
                    .isInstanceOf(DoctorNotFoundException.class)
                    .hasMessageContaining("존재하지 않거나 활성화되지 않은 의사입니다");
        }

        @Test
        @DisplayName("CalendarRequest가 null인 경우 NullPointerException 발생")
        void getReservationDates_NullRequest_ThrowsException() {
            // when & then
            assertThatThrownBy(() -> reservationService.getReservationDates(TEST_DOCTOR_ID, null))
                    .isInstanceOf(NullPointerException.class);
        }
    }

    @Nested
    @DisplayName("getReservationDates - 경계값 테스트")
    class getReservationDatesBoundaryTests {

        @Test
        @DisplayName("최소 연도(2000) 조회 성공")
        void getReservationDates_MinYear_Success() {
            // given
            CalendarRequest request = new CalendarRequest(2000, 1);
            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    any(UUID.class),
                    any(ReservationStatus.class),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(Collections.emptyList());

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response).isNotNull();
            assertThat(response.data()).isEmpty();
        }

        @Test
        @DisplayName("최대 연도(2100) 조회 성공")
        void getReservationDates_MaxYear_Success() {
            // given
            CalendarRequest request = new CalendarRequest(2100, 12);
            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    any(UUID.class),
                    any(ReservationStatus.class),
                    any(LocalDateTime.class),
                    any(LocalDateTime.class)
            )).willReturn(Collections.emptyList());

            // when
            CalendarReservationResponse response = reservationService.getReservationDates(TEST_DOCTOR_ID, request);

            // then
            assertThat(response).isNotNull();
            assertThat(response.data()).isEmpty();
        }
    }

    // 기존 Nested 클래스들 아래에 추가

    @Nested
    @DisplayName("getHospitalReservationDates - 병원별 예약 날짜 조회")
    class GetHospitalReservationDates {

        @Test
        @DisplayName("성공: 특정 병원의 특정 년/월 예약 날짜 목록을 조회한다")
        void getHospitalReservationDates_Success() {
            // given
            UUID hospitalId = UUID.randomUUID();
            int year = 2026;
            int month = 1;

            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 1, 5, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 5, 14, 0)), // 같은 날짜
                    createReservation(LocalDateTime.of(2026, 1, 12, 11, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 20, 15, 30))
            );

            given(reservationRepository.findReservationsByHospitalAndMonth(
                    eq(hospitalId), any(LocalDateTime.class), any(LocalDateTime.class)))
                    .willReturn(mockReservations);

            // when
            List<LocalDate> results = reservationService.getHospitalReservationDates(hospitalId, year, month);

            // then
            assertThat(results).hasSize(3); // 중복 제거되어 3개
            assertThat(results).containsExactly(
                    LocalDate.of(2026, 1, 5),
                    LocalDate.of(2026, 1, 12),
                    LocalDate.of(2026, 1, 20)
            );

            verify(reservationRepository, times(1))
                    .findReservationsByHospitalAndMonth(eq(hospitalId), any(LocalDateTime.class), any(LocalDateTime.class));
        }

        @Test
        @DisplayName("성공: 예약이 없는 월은 빈 리스트를 반환한다")
        void getHospitalReservationDates_EmptyResult() {
            // given
            UUID hospitalId = UUID.randomUUID();
            int year = 2026;
            int month = 12;

            given(reservationRepository.findReservationsByHospitalAndMonth(
                    eq(hospitalId), any(LocalDateTime.class), any(LocalDateTime.class)))
                    .willReturn(Collections.emptyList());

            // when
            List<LocalDate> results = reservationService.getHospitalReservationDates(hospitalId, year, month);

            // then
            assertThat(results).isEmpty();
        }

        @Test
        @DisplayName("성공: 날짜가 정렬되어 반환된다")
        void getHospitalReservationDates_Sorted() {
            // given
            UUID hospitalId = UUID.randomUUID();
            int year = 2026;
            int month = 1;

            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 1, 20, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 5, 14, 0)),
                    createReservation(LocalDateTime.of(2026, 1, 12, 11, 0))
            );

            given(reservationRepository.findReservationsByHospitalAndMonth(
                    eq(hospitalId), any(LocalDateTime.class), any(LocalDateTime.class)))
                    .willReturn(mockReservations);

            // when
            List<LocalDate> results = reservationService.getHospitalReservationDates(hospitalId, year, month);

            // then
            assertThat(results).containsExactly(
                    LocalDate.of(2026, 1, 5),
                    LocalDate.of(2026, 1, 12),
                    LocalDate.of(2026, 1, 20)
            );
        }

        @Test
        @DisplayName("성공: 2월의 범위를 정확하게 계산한다")
        void getHospitalReservationDates_FebruaryRange() {
            // given
            UUID hospitalId = UUID.randomUUID();
            int year = 2026;
            int month = 2;

            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 2, 14, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 2, 28, 14, 0))
            );

            given(reservationRepository.findReservationsByHospitalAndMonth(
                    eq(hospitalId), any(LocalDateTime.class), any(LocalDateTime.class)))
                    .willReturn(mockReservations);

            // when
            List<LocalDate> results = reservationService.getHospitalReservationDates(hospitalId, year, month);

            // then
            assertThat(results).hasSize(2);
            assertThat(results).containsExactly(
                    LocalDate.of(2026, 2, 14),
                    LocalDate.of(2026, 2, 28)
            );
        }

        @Test
        @DisplayName("성공: 12월의 범위를 정확하게 계산한다")
        void getHospitalReservationDates_DecemberRange() {
            // given
            UUID hospitalId = UUID.randomUUID();
            int year = 2026;
            int month = 12;

            List<Reservation> mockReservations = Arrays.asList(
                    createReservation(LocalDateTime.of(2026, 12, 24, 10, 0)),
                    createReservation(LocalDateTime.of(2026, 12, 31, 23, 59))
            );

            given(reservationRepository.findReservationsByHospitalAndMonth(
                    eq(hospitalId), any(LocalDateTime.class), any(LocalDateTime.class)))
                    .willReturn(mockReservations);

            // when
            List<LocalDate> results = reservationService.getHospitalReservationDates(hospitalId, year, month);

            // then
            assertThat(results).hasSize(2);
            assertThat(results).containsExactly(
                    LocalDate.of(2026, 12, 24),
                    LocalDate.of(2026, 12, 31)
            );
        }
    }

    // Helper method
    private Reservation createReservation(LocalDateTime scheduledAt) {
        return Reservation.builder()
                .scheduledAt(scheduledAt)
                .doctorId(TEST_DOCTOR_ID)
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();
    }
}