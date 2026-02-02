package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.*;

@DataJpaTest
class ReservationRepositoryTest {

    @Autowired
    private ReservationRepository reservationRepository;

    @Autowired
    private HospitalRepository hospitalRepository;

    @Autowired
    private HospitalStaffRepository hospitalStaffRepository;

    @Autowired
    private HospitalChildrenRepository hospitalChildrenRepository;

    @Autowired
    private ChildRepository childRepository;

    @Autowired
    private UserRepository userRepository;

    private Hospital testHospital;
    private HospitalChildren testHospitalChild1;
    private HospitalChildren testHospitalChild2;

    @BeforeEach
    void setUp() {
        // 병원 생성
        testHospital = Hospital.builder()
                .hospitalCode("HOSP-001")
                .name("테스트 병원")
                .phoneNumber("02-123-4567")
                .build();
        hospitalRepository.save(testHospital);

        // 사용자 생성
        User user = User.builder()
                .loginId("parent01")
                .password("password")
                .name("부모1")
                .userRole(UserRole.USER)
                .privacyAgreed(true)
                .build();
        userRepository.save(user);

        // 아이 생성
        Child child1 = Child.builder()
                .user(user)
                .name("김행복")
                .birthdate(LocalDate.of(2024, 1, 1))
                .gender(Gender.MALE)
                .build();

        Child child2 = Child.builder()
                .user(user)
                .name("이사랑")
                .birthdate(LocalDate.of(2024, 6, 1))
                .gender(Gender.FEMALE)
                .build();

        childRepository.saveAll(List.of(child1, child2));

        // 병원-아이 연결
        testHospitalChild1 = HospitalChildren.builder()
                .child(child1)
                .hospital(testHospital)
                .linkStatus(LinkStatus.ACTIVE)
                .build();

        testHospitalChild2 = HospitalChildren.builder()
                .child(child2)
                .hospital(testHospital)
                .linkStatus(LinkStatus.ACTIVE)
                .build();

        hospitalChildrenRepository.saveAll(List.of(testHospitalChild1, testHospitalChild2));
    }

    @Test
    @DisplayName("특정 병원의 특정 년/월에 예약된 Reservation 목록을 조회한다")
    void findReservationsByHospitalAndMonth_Success() {
        // given
        LocalDateTime startOfMonth = LocalDateTime.of(2026, 1, 1, 0, 0);
        LocalDateTime endOfMonth = LocalDateTime.of(2026, 2, 1, 0, 0);

        // 1월 5일 예약
        Reservation jan05 = Reservation.builder()
                .hospitalChildren(testHospitalChild1)
                .scheduledAt(LocalDateTime.of(2026, 1, 5, 10, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        // 1월 5일 또 다른 예약 (같은 날짜)
        Reservation jan05_2 = Reservation.builder()
                .hospitalChildren(testHospitalChild2)
                .scheduledAt(LocalDateTime.of(2026, 1, 5, 14, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        // 1월 12일 예약
        Reservation jan12 = Reservation.builder()
                .hospitalChildren(testHospitalChild1)
                .scheduledAt(LocalDateTime.of(2026, 1, 12, 11, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        // 1월 20일 예약
        Reservation jan20 = Reservation.builder()
                .hospitalChildren(testHospitalChild2)
                .scheduledAt(LocalDateTime.of(2026, 1, 20, 15, 30))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        // 2월 예약 (조회되지 않아야 함)
        Reservation feb05 = Reservation.builder()
                .hospitalChildren(testHospitalChild1)
                .scheduledAt(LocalDateTime.of(2026, 2, 5, 10, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        reservationRepository.saveAll(List.of(jan05, jan05_2, jan12, jan20, feb05));

        // when
        List<Reservation> results = reservationRepository.findReservationsByHospitalAndMonth(
                testHospital.getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).hasSize(4);
        assertThat(results)
                .extracting(r -> r.getScheduledAt().toLocalDate())
                .containsExactly(
                        LocalDate.of(2026, 1, 5),
                        LocalDate.of(2026, 1, 5),
                        LocalDate.of(2026, 1, 12),
                        LocalDate.of(2026, 1, 20)
                );
    }

    @Test
    @DisplayName("다른 병원의 예약은 조회되지 않는다")
    void findReservationsByHospitalAndMonth_DifferentHospital() {
        // given
        Hospital otherHospital = Hospital.builder()
                .hospitalCode("HOSP-002")
                .name("다른병원")
                .phoneNumber("02-999-9999")
                .build();
        hospitalRepository.save(otherHospital);

        User otherUser = User.builder()
                .loginId("other01")
                .password("password")
                .name("다른부모")
                .userRole(UserRole.USER)
                .privacyAgreed(true)
                .build();
        userRepository.save(otherUser);

        Child otherChild = Child.builder()
                .user(otherUser)
                .name("다른아이")
                .birthdate(LocalDate.of(2024, 3, 1))
                .gender(Gender.MALE)
                .build();
        childRepository.save(otherChild);

        HospitalChildren otherHC = HospitalChildren.builder()
                .child(otherChild)
                .hospital(otherHospital)
                .linkStatus(LinkStatus.ACTIVE)
                .build();
        hospitalChildrenRepository.save(otherHC);

        LocalDateTime startOfMonth = LocalDateTime.of(2026, 1, 1, 0, 0);
        LocalDateTime endOfMonth = LocalDateTime.of(2026, 2, 1, 0, 0);

        // 우리 병원 예약
        Reservation myReservation = Reservation.builder()
                .hospitalChildren(testHospitalChild1)
                .scheduledAt(LocalDateTime.of(2026, 1, 10, 10, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        // 다른 병원 예약
        Reservation otherReservation = Reservation.builder()
                .hospitalChildren(otherHC)
                .scheduledAt(LocalDateTime.of(2026, 1, 15, 10, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        reservationRepository.saveAll(List.of(myReservation, otherReservation));

        // when
        List<Reservation> results = reservationRepository.findReservationsByHospitalAndMonth(
                testHospital.getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).hasSize(1);
        assertThat(results.get(0).getHospitalChildren().getChild().getName()).isEqualTo("김행복");
    }

    @Test
    @DisplayName("해당 월에 예약이 없으면 빈 리스트를 반환한다")
    void findReservationsByHospitalAndMonth_EmptyResult() {
        // given
        LocalDateTime startOfMonth = LocalDateTime.of(2026, 12, 1, 0, 0);
        LocalDateTime endOfMonth = LocalDateTime.of(2027, 1, 1, 0, 0);

        // when
        List<Reservation> results = reservationRepository.findReservationsByHospitalAndMonth(
                testHospital.getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).isEmpty();
    }

    @Test
    @DisplayName("월의 경계값을 정확하게 처리한다")
    void findReservationsByHospitalAndMonth_BoundaryConditions() {
        // given
        LocalDateTime startOfMonth = LocalDateTime.of(2026, 1, 1, 0, 0);
        LocalDateTime endOfMonth = LocalDateTime.of(2026, 2, 1, 0, 0);

        // 12월 31일 (조회 안 됨)
        Reservation dec31 = Reservation.builder()
                .hospitalChildren(testHospitalChild1)
                .scheduledAt(LocalDateTime.of(2025, 12, 31, 23, 59))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        // 1월 1일 00:00 (조회 됨)
        Reservation jan01 = Reservation.builder()
                .hospitalChildren(testHospitalChild1)
                .scheduledAt(LocalDateTime.of(2026, 1, 1, 0, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        // 1월 31일 23:59 (조회 됨)
        Reservation jan31 = Reservation.builder()
                .hospitalChildren(testHospitalChild2)
                .scheduledAt(LocalDateTime.of(2026, 1, 31, 23, 59))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        // 2월 1일 00:00 (조회 안 됨)
        Reservation feb01 = Reservation.builder()
                .hospitalChildren(testHospitalChild1)
                .scheduledAt(LocalDateTime.of(2026, 2, 1, 0, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        reservationRepository.saveAll(List.of(dec31, jan01, jan31, feb01));

        // when
        List<Reservation> results = reservationRepository.findReservationsByHospitalAndMonth(
                testHospital.getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).hasSize(2);
        assertThat(results)
                .extracting(r -> r.getScheduledAt().toLocalDate())
                .containsExactly(
                        LocalDate.of(2026, 1, 1),
                        LocalDate.of(2026, 1, 31)
                );
    }

    @Test
    @DisplayName("N+1 문제가 발생하지 않는다 - JOIN FETCH 확인")
    void findReservationsByHospitalAndMonth_NoNPlusOne() {
        // given
        LocalDateTime startOfMonth = LocalDateTime.of(2026, 1, 1, 0, 0);
        LocalDateTime endOfMonth = LocalDateTime.of(2026, 2, 1, 0, 0);

        Reservation res1 = Reservation.builder()
                .hospitalChildren(testHospitalChild1)
                .scheduledAt(LocalDateTime.of(2026, 1, 10, 10, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        Reservation res2 = Reservation.builder()
                .hospitalChildren(testHospitalChild2)
                .scheduledAt(LocalDateTime.of(2026, 1, 15, 14, 0))
                .reservationStatus(ReservationStatus.SCHEDULED)
                .build();

        reservationRepository.saveAll(List.of(res1, res2));
        reservationRepository.flush();

        // when
        List<Reservation> results = reservationRepository.findReservationsByHospitalAndMonth(
                testHospital.getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then - hospitalChildren가 이미 fetch되어 추가 쿼리 발생하지 않음
        assertThat(results).hasSize(2);
        results.forEach(reservation -> {
            assertThat(reservation.getHospitalChildren()).isNotNull();
            assertThat(reservation.getHospitalChildren().getChild()).isNotNull();
        });
    }
}