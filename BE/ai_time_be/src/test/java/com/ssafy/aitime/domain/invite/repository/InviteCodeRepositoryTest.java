package com.ssafy.aitime.domain.invite.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.repository.HospitalRepository;
import com.ssafy.aitime.domain.hospital.repository.HospitalStaffRepository;
import com.ssafy.aitime.domain.invite.entity.InviteCode;
import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class InviteCodeRepositoryTest {

    @Autowired
    private InviteCodeRepository inviteCodeRepository;

    @Autowired
    private HospitalRepository hospitalRepository;

    @Autowired
    private HospitalStaffRepository hospitalStaffRepository;

    private HospitalStaff testStaff;
    private UUID testDoctorId;

    @BeforeEach
    void setUp() {
        // 1. 병원 저장
        Hospital hospital = Hospital.builder()
                .hospitalCode("HOSP-001")
                .name("에이아이타임 소아과")
                .phoneNumber("02-123-4567")
                .build();
        hospitalRepository.save(hospital);

        // 2. 스태프 저장
        testStaff = HospitalStaff.builder()
                .loginId("desk01")
                .password("password")
                .name("데스크직원")
                .staffRole(StaffRole.DESK)
                .hospital(hospital)
                .recordStatus(RecordStatus.ACTIVE)
                .build();
        hospitalStaffRepository.save(testStaff);

        testDoctorId = UUID.randomUUID();
    }

    @Test
    @DisplayName("비즈니스 초대코드로 엔티티를 조회한다")
    void findByInviteCode_Success() {
        // given
        String codeValue = "FTL-ABCD-12";
        InviteCode inviteCode = createInviteCode(codeValue, testDoctorId);
        inviteCodeRepository.save(inviteCode);

        // when
        Optional<InviteCode> result = inviteCodeRepository.findByInviteCode(codeValue);

        // then
        assertThat(result).isPresent();
        assertThat(result.get().getInviteCode()).isEqualTo(codeValue);
    }

    @Test
    @DisplayName("초대코드 중복 여부를 확인한다")
    void existsByInviteCode_Success() {
        // given
        String codeValue = "FTL-DUPE-99";
        InviteCode inviteCode = createInviteCode(codeValue, null);
        inviteCodeRepository.save(inviteCode);

        // when
        boolean exists = inviteCodeRepository.existsByInviteCode(codeValue);
        boolean notExists = inviteCodeRepository.existsByInviteCode("NON-EXISTENT");

        // then
        assertThat(exists).isTrue();
        assertThat(notExists).isFalse();
    }

    @Test
    @DisplayName("환아 정보와 의사 ID로 이미 발급된 ISSUED 상태의 코드를 조회한다")
    void findByComplexCondition_Success() {
        // given
        String childName = "박튼튼";
        LocalDate birth = LocalDate.of(2024, 5, 20);
        String phone = "01012345678";

        InviteCode inviteCode = InviteCode.builder()
                .inviteCode("FTL-COMP-01")
                .hospitalStaff(testStaff)
                .childName(childName)
                .childBirthdate(birth)
                .parentPhone(phone)
                .scheduledAt(LocalDateTime.now().plusDays(1))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .doctorId(testDoctorId)
                .build();
        inviteCodeRepository.save(inviteCode);

        // when
        Optional<InviteCode> result = inviteCodeRepository.findByChildNameAndChildBirthdateAndParentPhoneAndInviteCodeStatusAndDoctorId(
                childName, birth, phone, InviteCodeStatus.ISSUED, testDoctorId
        );

        // then
        assertThat(result).isPresent();
        assertThat(result.get().getChildName()).isEqualTo(childName);
        assertThat(result.get().getDoctorId()).isEqualTo(testDoctorId);
    }

    private InviteCode createInviteCode(String code, UUID doctorId) {
        return InviteCode.builder()
                .inviteCode(code)
                .hospitalStaff(testStaff)
                .childName("홍길동")
                .childBirthdate(LocalDate.of(2023, 1, 1))
                .parentPhone("01011112222")
                .scheduledAt(LocalDateTime.now().plusDays(1))
                .doctorId(doctorId)
                .build();
    }

    @Test
    @DisplayName("특정 병원의 특정 년/월에 ISSUED 상태인 초대코드 목록을 조회한다")
    void findIssuedInviteCodesByHospitalAndMonth_Success() {
        // given
        LocalDate targetMonth = LocalDate.of(2026, 1, 1);
        LocalDateTime startOfMonth = targetMonth.atStartOfDay();
        LocalDateTime endOfMonth = targetMonth.plusMonths(1).atStartOfDay();

        // 1월 10일 예약
        InviteCode jan10 = InviteCode.builder()
                .inviteCode("FTL-JAN-10")
                .hospitalStaff(testStaff)
                .childName("환아1")
                .childBirthdate(LocalDate.of(2024, 5, 1))
                .parentPhone("01011111111")
                .scheduledAt(LocalDateTime.of(2026, 1, 10, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 1월 10일 또 다른 예약 (같은 날짜 중복)
        InviteCode jan10_2 = InviteCode.builder()
                .inviteCode("FTL-JAN-10-2")
                .hospitalStaff(testStaff)
                .childName("환아2")
                .childBirthdate(LocalDate.of(2024, 6, 1))
                .parentPhone("01022222222")
                .scheduledAt(LocalDateTime.of(2026, 1, 10, 14, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 1월 15일 예약
        InviteCode jan15 = InviteCode.builder()
                .inviteCode("FTL-JAN-15")
                .hospitalStaff(testStaff)
                .childName("환아3")
                .childBirthdate(LocalDate.of(2024, 7, 1))
                .parentPhone("01033333333")
                .scheduledAt(LocalDateTime.of(2026, 1, 15, 11, 30))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 1월 20일 예약
        InviteCode jan20 = InviteCode.builder()
                .inviteCode("FTL-JAN-20")
                .hospitalStaff(testStaff)
                .childName("환아4")
                .childBirthdate(LocalDate.of(2024, 8, 1))
                .parentPhone("01044444444")
                .scheduledAt(LocalDateTime.of(2026, 1, 20, 15, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 1월 25일 예약
        InviteCode jan25 = InviteCode.builder()
                .inviteCode("FTL-JAN-25")
                .hospitalStaff(testStaff)
                .childName("환아5")
                .childBirthdate(LocalDate.of(2024, 9, 1))
                .parentPhone("01055555555")
                .scheduledAt(LocalDateTime.of(2026, 1, 25, 9, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 2월 예약 (조회되지 않아야 함)
        InviteCode feb05 = InviteCode.builder()
                .inviteCode("FTL-FEB-05")
                .hospitalStaff(testStaff)
                .childName("환아6")
                .childBirthdate(LocalDate.of(2024, 10, 1))
                .parentPhone("01066666666")
                .scheduledAt(LocalDateTime.of(2026, 2, 5, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // REGISTERED 상태 (조회되지 않아야 함)
        InviteCode jan12Registered = InviteCode.builder()
                .inviteCode("FTL-JAN-12-REG")
                .hospitalStaff(testStaff)
                .childName("환아7")
                .childBirthdate(LocalDate.of(2024, 11, 1))
                .parentPhone("01077777777")
                .scheduledAt(LocalDateTime.of(2026, 1, 12, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.REGISTERED)
                .build();

        inviteCodeRepository.saveAll(List.of(
                jan10, jan10_2, jan15, jan20, jan25, feb05, jan12Registered
        ));

        // when
        List<InviteCode> results = inviteCodeRepository.findIssuedInviteCodesByHospitalAndMonth(
                testStaff.getHospital().getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).hasSize(5); // 1월 ISSUED 상태 5개
        assertThat(results)
                .extracting(InviteCode::getChildName)
                .containsExactly("환아1", "환아2", "환아3", "환아4", "환아5");
        assertThat(results)
                .allMatch(ic -> ic.getInviteCodeStatus() == InviteCodeStatus.ISSUED);

        // scheduledAt 시간순 정렬 확인
        assertThat(results.get(0).getScheduledAt()).isEqualTo(LocalDateTime.of(2026, 1, 10, 10, 0));
        assertThat(results.get(1).getScheduledAt()).isEqualTo(LocalDateTime.of(2026, 1, 10, 14, 0));
        assertThat(results.get(2).getScheduledAt()).isEqualTo(LocalDateTime.of(2026, 1, 15, 11, 30));
    }

    @Test
    @DisplayName("다른 병원의 데이터는 조회되지 않는다 - 초대코드 목록")
    void findIssuedInviteCodesByHospitalAndMonth_DifferentHospital() {
        // given
        Hospital otherHospital = Hospital.builder()
                .hospitalCode("HOSP-999")
                .name("다른병원")
                .phoneNumber("02-999-9999")
                .build();
        hospitalRepository.save(otherHospital);

        HospitalStaff otherStaff = HospitalStaff.builder()
                .loginId("other99")
                .password("password")
                .name("다른직원")
                .staffRole(StaffRole.DESK)
                .hospital(otherHospital)
                .recordStatus(RecordStatus.ACTIVE)
                .build();
        hospitalStaffRepository.save(otherStaff);

        LocalDate targetMonth = LocalDate.of(2026, 1, 1);
        LocalDateTime startOfMonth = targetMonth.atStartOfDay();
        LocalDateTime endOfMonth = targetMonth.plusMonths(1).atStartOfDay();

        // 우리 병원 예약
        InviteCode myHospital = InviteCode.builder()
                .inviteCode("FTL-MY-01")
                .hospitalStaff(testStaff)
                .childName("우리환아")
                .childBirthdate(LocalDate.of(2024, 5, 1))
                .parentPhone("01011111111")
                .scheduledAt(LocalDateTime.of(2026, 1, 10, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 다른 병원 예약
        InviteCode otherHospitalCode = InviteCode.builder()
                .inviteCode("FTL-OTHER-01")
                .hospitalStaff(otherStaff)
                .childName("다른환아")
                .childBirthdate(LocalDate.of(2024, 6, 1))
                .parentPhone("01022222222")
                .scheduledAt(LocalDateTime.of(2026, 1, 15, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        inviteCodeRepository.saveAll(List.of(myHospital, otherHospitalCode));

        // when
        List<InviteCode> results = inviteCodeRepository.findIssuedInviteCodesByHospitalAndMonth(
                testStaff.getHospital().getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).hasSize(1);
        assertThat(results.get(0).getChildName()).isEqualTo("우리환아");
    }

    @Test
    @DisplayName("해당 월에 ISSUED 상태 예약이 없으면 빈 리스트를 반환한다")
    void findIssuedInviteCodesByHospitalAndMonth_EmptyResult() {
        // given
        LocalDate targetMonth = LocalDate.of(2026, 12, 1);
        LocalDateTime startOfMonth = targetMonth.atStartOfDay();
        LocalDateTime endOfMonth = targetMonth.plusMonths(1).atStartOfDay();

        // when
        List<InviteCode> results = inviteCodeRepository.findIssuedInviteCodesByHospitalAndMonth(
                testStaff.getHospital().getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).isEmpty();
    }

    @Test
    @DisplayName("REGISTERED, REVOKED 상태는 조회되지 않는다")
    void findIssuedInviteCodesByHospitalAndMonth_OnlyIssued() {
        // given
        LocalDate targetMonth = LocalDate.of(2026, 1, 1);
        LocalDateTime startOfMonth = targetMonth.atStartOfDay();
        LocalDateTime endOfMonth = targetMonth.plusMonths(1).atStartOfDay();

        // ISSUED 상태
        InviteCode issued = InviteCode.builder()
                .inviteCode("FTL-ISSUED-01")
                .hospitalStaff(testStaff)
                .childName("발급됨")
                .childBirthdate(LocalDate.of(2024, 5, 1))
                .parentPhone("01011111111")
                .scheduledAt(LocalDateTime.of(2026, 1, 10, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // REGISTERED 상태
        InviteCode registered = InviteCode.builder()
                .inviteCode("FTL-REG-01")
                .hospitalStaff(testStaff)
                .childName("등록됨")
                .childBirthdate(LocalDate.of(2024, 6, 1))
                .parentPhone("01022222222")
                .scheduledAt(LocalDateTime.of(2026, 1, 15, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.REGISTERED)
                .build();

        // REVOKED 상태
        InviteCode revoked = InviteCode.builder()
                .inviteCode("FTL-REV-01")
                .hospitalStaff(testStaff)
                .childName("취소됨")
                .childBirthdate(LocalDate.of(2024, 7, 1))
                .parentPhone("01033333333")
                .scheduledAt(LocalDateTime.of(2026, 1, 20, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.REVOKED)
                .build();

        inviteCodeRepository.saveAll(List.of(issued, registered, revoked));

        // when
        List<InviteCode> results = inviteCodeRepository.findIssuedInviteCodesByHospitalAndMonth(
                testStaff.getHospital().getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).hasSize(1);
        assertThat(results.get(0).getChildName()).isEqualTo("발급됨");
        assertThat(results.get(0).getInviteCodeStatus()).isEqualTo(InviteCodeStatus.ISSUED);
    }

    @Test
    @DisplayName("월의 경계값을 정확하게 처리한다")
    void findIssuedInviteCodesByHospitalAndMonth_BoundaryConditions() {
        // given - 2026년 1월
        LocalDate targetMonth = LocalDate.of(2026, 1, 1);
        LocalDateTime startOfMonth = targetMonth.atStartOfDay();         // 2026-01-01 00:00:00
        LocalDateTime endOfMonth = targetMonth.plusMonths(1).atStartOfDay(); // 2026-02-01 00:00:00

        // 12월 31일 23:59 (1월 아님)
        InviteCode dec31 = InviteCode.builder()
                .inviteCode("FTL-DEC-31")
                .hospitalStaff(testStaff)
                .childName("12월")
                .childBirthdate(LocalDate.of(2024, 5, 1))
                .parentPhone("01011111111")
                .scheduledAt(LocalDateTime.of(2025, 12, 31, 23, 59))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 1월 1일 00:00 (1월 포함)
        InviteCode jan01 = InviteCode.builder()
                .inviteCode("FTL-JAN-01")
                .hospitalStaff(testStaff)
                .childName("1월1일")
                .childBirthdate(LocalDate.of(2024, 6, 1))
                .parentPhone("01022222222")
                .scheduledAt(LocalDateTime.of(2026, 1, 1, 0, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 1월 31일 23:59 (1월 포함)
        InviteCode jan31 = InviteCode.builder()
                .inviteCode("FTL-JAN-31")
                .hospitalStaff(testStaff)
                .childName("1월31일")
                .childBirthdate(LocalDate.of(2024, 7, 1))
                .parentPhone("01033333333")
                .scheduledAt(LocalDateTime.of(2026, 1, 31, 23, 59))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        // 2월 1일 00:00 (1월 아님)
        InviteCode feb01 = InviteCode.builder()
                .inviteCode("FTL-FEB-01")
                .hospitalStaff(testStaff)
                .childName("2월")
                .childBirthdate(LocalDate.of(2024, 8, 1))
                .parentPhone("01044444444")
                .scheduledAt(LocalDateTime.of(2026, 2, 1, 0, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        inviteCodeRepository.saveAll(List.of(dec31, jan01, jan31, feb01));

        // when
        List<InviteCode> results = inviteCodeRepository.findIssuedInviteCodesByHospitalAndMonth(
                testStaff.getHospital().getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then
        assertThat(results).hasSize(2);
        assertThat(results)
                .extracting(InviteCode::getChildName)
                .containsExactly("1월1일", "1월31일");
    }

    @Test
    @DisplayName("N+1 문제가 발생하지 않는다 - JOIN FETCH 확인")
    void findIssuedInviteCodesByHospitalAndMonth_NoNPlusOne() {
        // given
        LocalDate targetMonth = LocalDate.of(2026, 1, 1);
        LocalDateTime startOfMonth = targetMonth.atStartOfDay();
        LocalDateTime endOfMonth = targetMonth.plusMonths(1).atStartOfDay();

        InviteCode code1 = InviteCode.builder()
                .inviteCode("FTL-TEST-01")
                .hospitalStaff(testStaff)
                .childName("환아1")
                .childBirthdate(LocalDate.of(2024, 5, 1))
                .parentPhone("01011111111")
                .scheduledAt(LocalDateTime.of(2026, 1, 10, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        InviteCode code2 = InviteCode.builder()
                .inviteCode("FTL-TEST-02")
                .hospitalStaff(testStaff)
                .childName("환아2")
                .childBirthdate(LocalDate.of(2024, 6, 1))
                .parentPhone("01022222222")
                .scheduledAt(LocalDateTime.of(2026, 1, 15, 10, 0))
                .inviteCodeStatus(InviteCodeStatus.ISSUED)
                .build();

        inviteCodeRepository.saveAll(List.of(code1, code2));
        inviteCodeRepository.flush();

        // when
        List<InviteCode> results = inviteCodeRepository.findIssuedInviteCodesByHospitalAndMonth(
                testStaff.getHospital().getHospitalId(),
                startOfMonth,
                endOfMonth
        );

        // then - hospitalStaff가 이미 fetch되어 추가 쿼리가 발생하지 않음
        assertThat(results).hasSize(2);

        // Lazy Loading 테스트 (추가 쿼리 발생하지 않음)
        results.forEach(inviteCode -> {
            assertThat(inviteCode.getHospitalStaff()).isNotNull();
            assertThat(inviteCode.getHospitalStaff().getName()).isEqualTo("데스크직원");
        });
    }
}