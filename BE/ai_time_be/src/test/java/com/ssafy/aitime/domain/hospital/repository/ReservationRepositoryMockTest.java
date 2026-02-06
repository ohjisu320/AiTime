package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.stereotype.Service;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;

@SpringBootTest(classes = ReservationRepositoryMockTest.TestService.class)
class ReservationRepositoryMockTest {

    @MockitoBean
    private ReservationRepository reservationRepository; // ✅ Mock로 대체됨

    @Autowired
    private TestService testService; // ✅ Spring이 주입

    @Test
    void findByDoctorIdAndReservationStatusNot_mocked() {
        // given
        UUID doctorId = UUID.randomUUID();

        Reservation r1 = Mockito.mock(Reservation.class);
        Reservation r2 = Mockito.mock(Reservation.class);

        given(reservationRepository.findByDoctorIdAndReservationStatusNot(
                eq(doctorId),
                eq(ReservationStatus.CANCELLED)
        )).willReturn(List.of(r1, r2));

        // when
        List<Reservation> result = testService.findNotCancelled(doctorId);

        // then
        assertThat(result).containsExactly(r1, r2);
    }

    @Test
    void findByDoctorIdAndReservationStatusNotAndScheduledAtBetween_mocked() {
        // given
        UUID doctorId = UUID.randomUUID();
        LocalDateTime start = LocalDateTime.of(2026, 1, 26, 0, 0);
        LocalDateTime end = LocalDateTime.of(2026, 1, 26, 23, 59, 59);

        Reservation r1 = Mockito.mock(Reservation.class);

        given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                eq(doctorId),
                eq(ReservationStatus.CANCELLED),
                eq(start),
                eq(end)
        )).willReturn(List.of(r1));

        // when
        List<Reservation> result = testService.findNotCancelledBetween(doctorId, start, end);

        // then
        assertThat(result).containsExactly(r1);
    }

    @Service
    static class TestService {
        private final ReservationRepository reservationRepository;

        TestService(ReservationRepository reservationRepository) {
            this.reservationRepository = reservationRepository;
        }

        List<Reservation> findNotCancelled(UUID doctorId) {
            return reservationRepository.findByDoctorIdAndReservationStatusNot(
                    doctorId, ReservationStatus.CANCELLED
            );
        }

        List<Reservation> findNotCancelledBetween(UUID doctorId, LocalDateTime start, LocalDateTime end) {
            return reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                    doctorId, ReservationStatus.CANCELLED, start, end
            );
        }
    }
}
