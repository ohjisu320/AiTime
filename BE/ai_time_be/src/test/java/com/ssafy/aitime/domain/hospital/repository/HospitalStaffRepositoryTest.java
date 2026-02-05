package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import jakarta.persistence.EntityManager;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@DisplayName("HospitalStaffRepository 테스트")
class HospitalStaffRepositoryTest {

    @Autowired
    private HospitalStaffRepository hospitalStaffRepository;

    @Autowired
    private HospitalRepository hospitalRepository;

    @Autowired
    private EntityManager em;

    @Test
    @DisplayName("loginId와 RecordStatus로 병원 직원을 조회할 수 있다")
    void findByLoginIdAndRecordStatus() {
        // given
        Hospital hospital = Hospital.builder()
                .hospitalCode("HOSP-001")
                .name("서울병원")
                .address("서울시 강남구")
                .phoneNumber("02-1234-5678")
                .build();
        hospitalRepository.save(hospital);

        HospitalStaff staff = HospitalStaff.builder()
                .hospital(hospital)
                .loginId("doctor01")
                .password("encodedPassword")
                .name("김의사")
                .email("doctor@hospital.com")
                .phoneNumber("010-1234-5678")
                .staffRole(StaffRole.DOCTOR)
                .recordStatus(RecordStatus.ACTIVE)
                .build();
        hospitalStaffRepository.save(staff);

        em.flush();
        em.clear();

        // when
        Optional<HospitalStaff> result = hospitalStaffRepository
                .findByLoginIdAndRecordStatus("doctor01", RecordStatus.ACTIVE);

        // then
        assertThat(result).isPresent();
        assertThat(result.get().getLoginId()).isEqualTo("doctor01");
        assertThat(result.get().getName()).isEqualTo("김의사");
        assertThat(result.get().getStaffRole()).isEqualTo(StaffRole.DOCTOR);
    }

    @Test
    @DisplayName("삭제된(DELETED) 직원은 조회되지 않는다")
    void findByLoginIdAndRecordStatus_Deleted() {
        // given
        Hospital hospital = Hospital.builder()
                .hospitalCode("HOSP-002")
                .name("서울병원")
                .address("서울시 강남구")
                .phoneNumber("02-1234-5678")
                .build();
        hospitalRepository.save(hospital);

        HospitalStaff staff = HospitalStaff.builder()
                .hospital(hospital)
                .loginId("deleted_doctor")
                .password("encodedPassword")
                .name("퇴사의사")
                .staffRole(StaffRole.DOCTOR)
                .recordStatus(RecordStatus.DELETED)
                .build();
        hospitalStaffRepository.save(staff);

        em.flush();
        em.clear();

        // when
        Optional<HospitalStaff> result = hospitalStaffRepository
                .findByLoginIdAndRecordStatus("deleted_doctor", RecordStatus.ACTIVE);

        // then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("존재하지 않는 loginId로 조회하면 빈 Optional을 반환한다")
    void findByLoginIdAndRecordStatus_NotFound() {
        // when
        Optional<HospitalStaff> result = hospitalStaffRepository
                .findByLoginIdAndRecordStatus("nonexistent", RecordStatus.ACTIVE);

        // then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("DOCTOR 역할과 ACTIVE 상태의 직원이 존재하면 true 반환")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_DoctorActive_ReturnsTrue() {
        // given
        Hospital hospital = persistHospital("HOSP-001", "서울병원", "서울특별시", "02-1234-5678", RecordStatus.ACTIVE);
        HospitalStaff doctor = persistHospitalStaff(hospital, "doctor1", "홍길동", "password", StaffRole.DOCTOR, RecordStatus.ACTIVE);

        em.flush();
        em.clear();

        // when
        boolean exists = hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                doctor.getHospitalStaffId(),
                StaffRole.DOCTOR,
                RecordStatus.ACTIVE
        );

        // then
        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("DESK 역할과 ACTIVE 상태의 직원이 존재하면 true 반환")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_DeskActive_ReturnsTrue() {
        // given
        Hospital hospital = persistHospital("HOSP-002", "부산병원", "부산광역시", "051-5678-9012", RecordStatus.ACTIVE);
        HospitalStaff desk = persistHospitalStaff(hospital, "desk1", "김철수", "password", StaffRole.DESK, RecordStatus.ACTIVE);

        em.flush();
        em.clear();

        // when
        boolean exists = hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                desk.getHospitalStaffId(),
                StaffRole.DESK,
                RecordStatus.ACTIVE
        );

        // then
        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("존재하지 않는 ID로 조회 시 false 반환")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_NotExist_ReturnsFalse() {
        // given
        UUID nonExistentId = UUID.randomUUID();

        // when
        boolean exists = hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                nonExistentId,
                StaffRole.DOCTOR,
                RecordStatus.ACTIVE
        );

        // then
        assertThat(exists).isFalse();
    }

    @Test
    @DisplayName("ID는 맞지만 역할이 다르면 false 반환")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_WrongRole_ReturnsFalse() {
        // given
        Hospital hospital = persistHospital("HOSP-003", "대전병원", "대전광역시", "042-3456-7890", RecordStatus.ACTIVE);
        HospitalStaff doctor = persistHospitalStaff(hospital, "doctor2", "이영희", "password", StaffRole.DOCTOR, RecordStatus.ACTIVE);

        em.flush();
        em.clear();

        // when - DOCTOR인데 DESK로 조회
        boolean exists = hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                doctor.getHospitalStaffId(),
                StaffRole.DESK,
                RecordStatus.ACTIVE
        );

        // then
        assertThat(exists).isFalse();
    }

    @Test
    @DisplayName("ID와 역할은 맞지만 DELETED 상태면 false 반환")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_DeletedStatus_ReturnsFalse() {
        // given
        Hospital hospital = persistHospital("HOSP-004", "광주병원", "광주광역시", "062-7890-1234", RecordStatus.ACTIVE);
        HospitalStaff deletedDoctor = persistHospitalStaff(hospital, "doctor3", "박민수", "password", StaffRole.DOCTOR, RecordStatus.DELETED);

        em.flush();
        em.clear();

        // when - DELETED 상태인데 ACTIVE로 조회
        boolean exists = hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                deletedDoctor.getHospitalStaffId(),
                StaffRole.DOCTOR,
                RecordStatus.ACTIVE
        );

        // then
        assertThat(exists).isFalse();
    }

    @Test
    @DisplayName("DELETED 상태의 의사를 DELETED로 조회하면 true 반환")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_DeletedDoctor_ReturnsTrue() {
        // given
        Hospital hospital = persistHospital("HOSP-005", "인천병원", "인천광역시", "032-2345-6789", RecordStatus.ACTIVE);
        HospitalStaff deletedDoctor = persistHospitalStaff(hospital, "doctor4", "최지훈", "password", StaffRole.DOCTOR, RecordStatus.DELETED);

        em.flush();
        em.clear();

        // when
        boolean exists = hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                deletedDoctor.getHospitalStaffId(),
                StaffRole.DOCTOR,
                RecordStatus.DELETED
        );

        // then
        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("모든 조건이 일치하지 않으면 false 반환")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_AllWrong_ReturnsFalse() {
        // given
        Hospital hospital = persistHospital("HOSP-006", "울산병원", "울산광역시", "052-4567-8901", RecordStatus.ACTIVE);
        HospitalStaff doctor = persistHospitalStaff(hospital, "doctor5", "정수아", "password", StaffRole.DOCTOR, RecordStatus.ACTIVE);

        em.flush();
        em.clear();

        // when - 다른 ID, 다른 역할로 조회
        boolean exists = hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                UUID.randomUUID(),
                StaffRole.DESK,
                RecordStatus.ACTIVE
        );

        // then
        assertThat(exists).isFalse();
    }

    @Test
    @DisplayName("여러 직원이 있을 때 특정 조건의 직원만 정확히 찾음")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_MultipleStaff_FindsCorrectOne() {
        // given
        Hospital hospital = persistHospital("HOSP-007", "대구병원", "대구광역시", "053-5678-9012", RecordStatus.ACTIVE);

        HospitalStaff doctor1 = persistHospitalStaff(hospital, "doctor6", "강민지", "password", StaffRole.DOCTOR, RecordStatus.ACTIVE);
        HospitalStaff doctor2 = persistHospitalStaff(hospital, "doctor7", "송하늘", "password", StaffRole.DOCTOR, RecordStatus.DELETED);
        HospitalStaff desk1 = persistHospitalStaff(hospital, "desk2", "한지원", "password", StaffRole.DESK, RecordStatus.ACTIVE);

        em.flush();
        em.clear();

        // when & then - ACTIVE DOCTOR
        assertThat(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                doctor1.getHospitalStaffId(),
                StaffRole.DOCTOR,
                RecordStatus.ACTIVE
        )).isTrue();

        // when & then - DELETED DOCTOR
        assertThat(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                doctor2.getHospitalStaffId(),
                StaffRole.DOCTOR,
                RecordStatus.DELETED
        )).isTrue();

        // when & then - ACTIVE DESK
        assertThat(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                desk1.getHospitalStaffId(),
                StaffRole.DESK,
                RecordStatus.ACTIVE
        )).isTrue();

        // when & then - DELETED DOCTOR를 ACTIVE로 조회
        assertThat(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                doctor2.getHospitalStaffId(),
                StaffRole.DOCTOR,
                RecordStatus.ACTIVE
        )).isFalse();
    }

    @Test
    @DisplayName("같은 병원에 여러 의사가 있을 때 각각 정확히 구분")
    void existsByHospitalStaffIdAndStaffRoleAndRecordStatus_MultipleDoctors_DistinguishesEach() {
        // given
        Hospital hospital = persistHospital("HOSP-008", "제주병원", "제주도", "064-6789-0123", RecordStatus.ACTIVE);

        HospitalStaff doctor1 = persistHospitalStaff(hospital, "doctor8", "권태양", "password", StaffRole.DOCTOR, RecordStatus.ACTIVE);
        HospitalStaff doctor2 = persistHospitalStaff(hospital, "doctor9", "오별", "password", StaffRole.DOCTOR, RecordStatus.ACTIVE);

        em.flush();
        em.clear();

        // when & then - 첫 번째 의사
        assertThat(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                doctor1.getHospitalStaffId(),
                StaffRole.DOCTOR,
                RecordStatus.ACTIVE
        )).isTrue();

        // when & then - 두 번째 의사
        assertThat(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                doctor2.getHospitalStaffId(),
                StaffRole.DOCTOR,
                RecordStatus.ACTIVE
        )).isTrue();

        // when & then - 첫 번째 의사 ID로 두 번째 의사는 찾을 수 없음
        assertThat(doctor1.getHospitalStaffId()).isNotEqualTo(doctor2.getHospitalStaffId());
    }

    // ----------------- helpers -----------------

    private Hospital persistHospital(String code, String name, String address, String phoneNumber, RecordStatus status) {
        Hospital hospital = Hospital.builder()
                .hospitalCode(code)
                .name(name)
                .address(address)
                .phoneNumber(phoneNumber)
                .recordStatus(status)
                .build();
        em.persist(hospital);
        return hospital;
    }

    private HospitalStaff persistHospitalStaff(Hospital hospital, String loginId, String name,
                                               String password, StaffRole role, RecordStatus status) {
        HospitalStaff staff = HospitalStaff.builder()
                .hospital(hospital)
                .loginId(loginId)
                .name(name)
                .password(password)
                .staffRole(role)
                .recordStatus(status)
                .build();
        em.persist(staff);
        return staff;
    }

    @Test
    @DisplayName("특정 병원에 소속된 ACTIVE 상태의 의사들만 조회한다")
    void findAllByHospital_HospitalIdAndStaffRoleAndRecordStatus_Success() {
        // given
        Hospital hospital1 = persistHospital("H1", "병원1", "주소", "02-1", RecordStatus.ACTIVE);
        Hospital hospital2 = persistHospital("H2", "병원2", "주소", "02-2", RecordStatus.ACTIVE);

        // 병원 1의 의사들
        persistHospitalStaff(hospital1, "doc1", "박의사", "pw", StaffRole.DOCTOR, RecordStatus.ACTIVE);
        persistHospitalStaff(hospital1, "doc2", "김의사", "pw", StaffRole.DOCTOR, RecordStatus.ACTIVE);

        // 병원 1의 데스크 (조회되면 안됨)
        persistHospitalStaff(hospital1, "desk1", "접수원", "pw", StaffRole.DESK, RecordStatus.ACTIVE);

        // 병원 2의 의사 (조회되면 안됨)
        persistHospitalStaff(hospital2, "doc3", "남의병원 의사", "pw", StaffRole.DOCTOR, RecordStatus.ACTIVE);

        em.flush();
        em.clear();

        // when
        List<HospitalStaff> results = hospitalStaffRepository
                .findAllByHospital_HospitalIdAndStaffRoleAndRecordStatus(
                        hospital1.getHospitalId(), StaffRole.DOCTOR, RecordStatus.ACTIVE);

        // then
        assertThat(results).hasSize(2);
        assertThat(results).extracting("name").containsExactlyInAnyOrder("박의사", "김의사");
        assertThat(results).extracting("hospital.hospitalId").containsOnly(hospital1.getHospitalId());
    }
}