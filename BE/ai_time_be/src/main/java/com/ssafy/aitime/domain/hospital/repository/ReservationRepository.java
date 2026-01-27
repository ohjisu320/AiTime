package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

@Repository
public interface ReservationRepository extends JpaRepository<Reservation, UUID> {

    /**
     * 특정 의사의 예약 목록 조회 (특정 상태 제외)
     */
    List<Reservation> findByDoctorIdAndReservationStatusNot(
            UUID doctorId,
            ReservationStatus reservationStatus);


    /**
     * 특정 의사의 특정 기간 예약 목록 조회 (특정 상태 제외)
     */
    List<Reservation> findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
            UUID doctorId,
            ReservationStatus reservationStatus,
            LocalDateTime startOfDay,
            LocalDateTime endOfDay);
}
