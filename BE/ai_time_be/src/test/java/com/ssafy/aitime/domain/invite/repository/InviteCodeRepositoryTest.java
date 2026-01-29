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
}