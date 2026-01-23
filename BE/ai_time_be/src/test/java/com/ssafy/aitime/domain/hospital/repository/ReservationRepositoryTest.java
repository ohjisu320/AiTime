package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.user.entity.User;
import jakarta.persistence.EntityManager;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class ReservationRepositoryTest {

    @Autowired
    ReservationRepository reservationRepository;

    @Autowired
    EntityManager em;

    @Test
    @DisplayName("doctorId로 조회하되 reservationStatusNot(CANCELLED) 조건이 적용된다")
    void findByDoctorIdAndReservationStatusNot_excludesCancelled() {
        // given
        UUID doctorId = UUID.randomUUID();
        UUID otherDoctorId = UUID.randomUUID();

        User user = persistUser();
        Hospital hospital = persistHospital("HOSP-" + UUID.randomUUID(), "병원A", "서울", RecordStatus.ACTIVE);

        Child child1 = persistChild(user, "아이1", LocalDate.of(2024, 1, 1), Gender.MALE, RecordStatus.ACTIVE);
        Child child2 = persistChild(user, "아이2", LocalDate.of(2024, 2, 1), Gender.FEMALE, RecordStatus.ACTIVE);

        HospitalChildren hc1 = persistHospitalChildren(child1, hospital, LinkStatus.ACTIVE);
        HospitalChildren hc2 = persistHospitalChildren(child2, hospital, LinkStatus.ACTIVE);

        Reservation rScheduled = persistReservation(hc1, doctorId, ReservationStatus.SCHEDULED, LocalDateTime.now().plusDays(1));
        Reservation rDone      = persistReservation(hc2, doctorId, ReservationStatus.DONE, LocalDateTime.now().minusDays(1));
        Reservation rCancelled = persistReservation(hc1, doctorId, ReservationStatus.CANCELLED, LocalDateTime.now().plusDays(2));

        // 다른 doctor 건도 하나 섞기
        Reservation otherDoctorReservation = persistReservation(hc1, otherDoctorId, ReservationStatus.SCHEDULED, LocalDateTime.now().plusDays(3));

        em.flush();
        em.clear();

        // when
        List<Reservation> result = reservationRepository
                .findByDoctorIdAndReservationStatusNot(doctorId, ReservationStatus.CANCELLED);

        // then
        assertThat(result)
                .extracting(Reservation::getReservationId)
                .contains(rScheduled.getReservationId(), rDone.getReservationId())
                .doesNotContain(rCancelled.getReservationId(), otherDoctorReservation.getReservationId());

        // 안전하게 상태도 검증
        assertThat(result).allMatch(r -> r.getDoctorId().equals(doctorId));
        assertThat(result).noneMatch(r -> r.getReservationStatus() == ReservationStatus.CANCELLED);
    }

    @Test
    @DisplayName("해당 doctorId가 없으면 빈 리스트")
    void findByDoctorIdAndReservationStatusNot_empty() {
        // when
        List<Reservation> result = reservationRepository
                .findByDoctorIdAndReservationStatusNot(UUID.randomUUID(), ReservationStatus.CANCELLED);

        // then
        assertThat(result).isEmpty();
    }

    // ----------------- helpers -----------------

    private Reservation persistReservation(HospitalChildren hc, UUID doctorId, ReservationStatus status, LocalDateTime scheduledAt) {
        Reservation reservation = Reservation.builder()
                .hospitalChildren(hc)
                .doctorId(doctorId)
                .reservationStatus(status)
                .scheduledAt(scheduledAt)
                .build();
        em.persist(reservation);
        return reservation;
    }

    private Hospital persistHospital(String code, String name, String address, RecordStatus status) {
        Hospital hospital = Hospital.builder()
                .hospitalCode(code)
                .name(name)
                .address(address)
                .recordStatus(status)
                .build();
        em.persist(hospital);
        return hospital;
    }

    private Child persistChild(User user, String name, LocalDate birthdate, Gender gender, RecordStatus status) {
        Child child = Child.builder()
                .user(user)
                .name(name)
                .birthdate(birthdate)
                .gender(gender)
                .recordStatus(status)
                .build();
        em.persist(child);
        return child;
    }

    private HospitalChildren persistHospitalChildren(Child child, Hospital hospital, LinkStatus linkStatus) {
        HospitalChildren hc = HospitalChildren.builder()
                .child(child)
                .hospital(hospital)
                .linkStatus(linkStatus)
                .build();
        em.persist(hc);
        return hc;
    }

    private User persistUser() {
        User user = User.builder()
                .loginId("test_" + UUID.randomUUID())
                .password("pw")
                .name("테스트유저")
                .build();
        em.persist(user);
        return user;
    }
}
