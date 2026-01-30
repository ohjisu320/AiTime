package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
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

    @Query("""
        SELECT r FROM Reservation r
        JOIN FETCH r.hospitalChildren hc
        WHERE hc.hospital.hospitalId = :hospitalId
        AND r.scheduledAt >= :startOfMonth
        AND r.scheduledAt < :endOfMonth
        ORDER BY r.scheduledAt ASC
    """)
    List<Reservation> findReservationsByHospitalAndMonth(
            @Param("hospitalId") UUID hospitalId,
            @Param("startOfMonth") LocalDateTime startOfMonth,
            @Param("endOfMonth") LocalDateTime endOfMonth
    );
}
