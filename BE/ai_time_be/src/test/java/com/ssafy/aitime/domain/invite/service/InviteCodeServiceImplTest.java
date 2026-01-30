package com.ssafy.aitime.domain.invite.service;

import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.exception.HospitalStaffAccessDeniedException;
import com.ssafy.aitime.domain.hospital.exception.InvalidDoctorSelectionException;
import com.ssafy.aitime.domain.hospital.service.HospitalStaffService;
import com.ssafy.aitime.domain.invite.dto.request.InviteCodeRequest;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeResponse;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeRevokeResponse;
import com.ssafy.aitime.domain.invite.dto.response.UnregisteredPatientResponse;
import com.ssafy.aitime.domain.invite.entity.InviteCode;
import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import com.ssafy.aitime.domain.invite.exception.AlreadyIssuedInviteCodeException;
import com.ssafy.aitime.domain.invite.exception.InviteCodeAlreadyUsedException;
import com.ssafy.aitime.domain.invite.exception.InviteCodeNotFoundException;
import com.ssafy.aitime.domain.invite.repository.InviteCodeRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class InviteCodeServiceImplTest {

    @Mock
    private InviteCodeRepository inviteCodeRepository;

    @Mock
    private HospitalStaffService hospitalStaffService;

    @InjectMocks
    private InviteCodeServiceImpl inviteCodeService;

    private Hospital testHospital;
    private HospitalStaff deskStaff;
    private UUID staffId;

    @BeforeEach
    void setUp() {
        staffId = UUID.randomUUID();
        testHospital = Hospital.builder().name("Aitime 병원").build();
        ReflectionTestUtils.setField(testHospital, "hospitalId", UUID.randomUUID());

        deskStaff = HospitalStaff.builder()
                .staffRole(StaffRole.DESK)
                .hospital(testHospital)
                .build();
        ReflectionTestUtils.setField(deskStaff, "hospitalStaffId", staffId);
    }

    @Nested
    @DisplayName("초대코드 생성 테스트")
    class GenerateInviteCode {

        @Test
        @DisplayName("성공: 데스크 직원이 유효한 요청을 보내면 초대코드가 생성된다")
        void generate_Success() {
            // given
            InviteCodeRequest request = createRequest(null);
            given(hospitalStaffService.getHospitalStaffById(staffId)).willReturn(deskStaff);
            given(inviteCodeRepository.findByChildNameAndChildBirthdateAndParentPhoneAndInviteCodeStatusAndDoctorId(
                    anyString(), any(), anyString(), any(), any()))
                    .willReturn(Optional.empty());
            given(inviteCodeRepository.existsByInviteCode(anyString())).willReturn(false);

            InviteCode savedEntity = InviteCode.builder()
                    .inviteCode("FTL-TEST-01")
                    .childName(request.childName())
                    .inviteCodeStatus(InviteCodeStatus.ISSUED)
                    .build();
            ReflectionTestUtils.setField(savedEntity, "inviteCodeId", UUID.randomUUID());
            given(inviteCodeRepository.save(any(InviteCode.class))).willReturn(savedEntity);

            // when
            InviteCodeResponse response = inviteCodeService.generateInviteCode(request, staffId);

            // then
            assertThat(response.childName()).isEqualTo(request.childName());
            assertThat(response.status()).isEqualTo(InviteCodeStatus.ISSUED);
            verify(inviteCodeRepository, times(1)).save(any(InviteCode.class));
        }

        @Test
        @DisplayName("실패: 데스크 직원이 아닌 경우 예외가 발생한다")
        void generate_Fail_NotDesk() {
            // given
            HospitalStaff doctorStaff = HospitalStaff.builder().staffRole(StaffRole.DOCTOR).build();
            given(hospitalStaffService.getHospitalStaffById(staffId)).willReturn(doctorStaff);

            // when & then
            assertThatThrownBy(() -> inviteCodeService.generateInviteCode(createRequest(null), staffId))
                    .isInstanceOf(HospitalStaffAccessDeniedException.class);
        }

        @Test
        @DisplayName("실패: 이미 해당 의사로 발급된 대기 중인 코드가 있으면 예외가 발생한다")
        void generate_Fail_AlreadyIssued() {
            // given
            InviteCodeRequest request = createRequest(UUID.randomUUID());
            given(hospitalStaffService.getHospitalStaffById(staffId)).willReturn(deskStaff);
            // 의사 정보 모킹 (같은 병원)
            HospitalStaff doctor = HospitalStaff.builder().staffRole(StaffRole.DOCTOR).hospital(testHospital).build();
            given(hospitalStaffService.getHospitalStaffById(request.doctorId())).willReturn(doctor);

            given(inviteCodeRepository.findByChildNameAndChildBirthdateAndParentPhoneAndInviteCodeStatusAndDoctorId(
                    any(), any(), any(), any(), any()))
                    .willReturn(Optional.of(mock(InviteCode.class)));

            // when & then
            assertThatThrownBy(() -> inviteCodeService.generateInviteCode(request, staffId))
                    .isInstanceOf(AlreadyIssuedInviteCodeException.class);
        }
    }

    @Nested
    @DisplayName("초대코드 취소 테스트")
    class RevokeInviteCode {

        @Test
        @DisplayName("성공: 미사용 초대코드를 취소하면 상태가 REVOKED로 변경된다")
        void revoke_Success() {
            // given
            UUID inviteCodeId = UUID.randomUUID();
            InviteCode inviteCode = InviteCode.builder()
                    .inviteCodeStatus(InviteCodeStatus.ISSUED)
                    .hospitalStaff(deskStaff)
                    .build();
            ReflectionTestUtils.setField(inviteCode, "inviteCodeId", inviteCodeId);

            given(hospitalStaffService.getHospitalStaffById(staffId)).willReturn(deskStaff);
            given(inviteCodeRepository.findById(inviteCodeId)).willReturn(Optional.of(inviteCode));
            given(inviteCodeRepository.save(any())).willReturn(inviteCode);

            // when
            InviteCodeRevokeResponse response = inviteCodeService.revokeInviteCode(inviteCodeId, staffId);

            // then
            assertThat(response.status()).isEqualTo(InviteCodeStatus.REVOKED);
            assertThat(inviteCode.getInviteCodeStatus()).isEqualTo(InviteCodeStatus.REVOKED);
        }

        @Test
        @DisplayName("실패: 다른 스태프가 발급한 초대코드는 취소할 수 없다")
        void revoke_Fail_OtherStaff() {
            // given
            UUID inviteCodeId = UUID.randomUUID();
            HospitalStaff otherStaff = HospitalStaff.builder().build();
            ReflectionTestUtils.setField(otherStaff, "hospitalStaffId", UUID.randomUUID()); // 다른 ID

            InviteCode inviteCode = InviteCode.builder()
                    .inviteCodeStatus(InviteCodeStatus.ISSUED)
                    .hospitalStaff(otherStaff) // 발급자를 다른 사람으로 설정
                    .build();

            given(hospitalStaffService.getHospitalStaffById(staffId)).willReturn(deskStaff);
            given(inviteCodeRepository.findById(inviteCodeId)).willReturn(Optional.of(inviteCode));

            // when & then
            assertThatThrownBy(() -> inviteCodeService.revokeInviteCode(inviteCodeId, staffId))
                    .isInstanceOf(HospitalStaffAccessDeniedException.class);
        }

        @Test
        @DisplayName("실패: 이미 사용된(REGISTERED) 코드는 취소할 수 없다")
        void revoke_Fail_AlreadyUsed() {
            // given
            UUID inviteCodeId = UUID.randomUUID();
            InviteCode inviteCode = InviteCode.builder()
                    .inviteCodeStatus(InviteCodeStatus.REGISTERED) // ✅ 핵심: 사용된 상태로!
                    .hospitalStaff(deskStaff)
                    .build();
            ReflectionTestUtils.setField(inviteCode, "inviteCodeId", inviteCodeId);

            given(hospitalStaffService.getHospitalStaffById(staffId)).willReturn(deskStaff);
            given(inviteCodeRepository.findById(inviteCodeId)).willReturn(Optional.of(inviteCode));

            // when & then
            assertThatThrownBy(() -> inviteCodeService.revokeInviteCode(inviteCodeId, staffId))
                    .isInstanceOf(InviteCodeAlreadyUsedException.class);

            // (선택) save가 호출되지 않았는지까지 검증 가능
            verify(inviteCodeRepository, never()).save(any());
        }
    }

    private InviteCodeRequest createRequest(UUID doctorId) {
        return new InviteCodeRequest(
                "박튼튼",
                LocalDate.of(2024, 5, 20),
                "01012345678",
                LocalDateTime.now().plusDays(1),
                doctorId
        );
    }

    @Nested
    @DisplayName("날짜별 등록 대기 환아 목록 조회 테스트")
    class GetUnregisteredPatients {

        @Test
        @DisplayName("성공: 특정 날짜의 미등록 환아 목록을 조회한다")
        void getUnregisteredPatients_Success() {
            // given
            UUID hospitalId = testHospital.getHospitalId();
            int year = 2026;
            int month = 1;
            int day = 20;
            LocalDate targetDate = LocalDate.of(year, month, day);

            // 테스트 데이터 - 14개월 된 아이 (2024년 11월 20일생)
            InviteCode inviteCode1 = InviteCode.builder()
                    .inviteCode("FTL-TEST-01")
                    .hospitalStaff(deskStaff)
                    .childName("박튼튼")
                    .childBirthdate(LocalDate.of(2024, 11, 20))
                    .parentPhone("01012345678")
                    .scheduledAt(LocalDateTime.of(2026, 1, 20, 10, 0))
                    .inviteCodeStatus(InviteCodeStatus.ISSUED)
                    .build();
            ReflectionTestUtils.setField(inviteCode1, "inviteCodeId", UUID.randomUUID());

            // 테스트 데이터 - 19개월 된 아이 (2024년 6월 15일생)
            InviteCode inviteCode2 = InviteCode.builder()
                    .inviteCode("FTL-TEST-02")
                    .hospitalStaff(deskStaff)
                    .childName("김건강")
                    .childBirthdate(LocalDate.of(2024, 6, 15))
                    .parentPhone("01087654321")
                    .scheduledAt(LocalDateTime.of(2026, 1, 20, 14, 30))
                    .inviteCodeStatus(InviteCodeStatus.ISSUED)
                    .build();
            ReflectionTestUtils.setField(inviteCode2, "inviteCodeId", UUID.randomUUID());

            given(inviteCodeRepository.findUnregisteredPatientsByHospitalAndDate(hospitalId, targetDate))
                    .willReturn(List.of(inviteCode1, inviteCode2));

            // when
            List<UnregisteredPatientResponse> results = inviteCodeService
                    .getUnregisteredPatients(hospitalId, year, month, day);

            // then
            assertThat(results).hasSize(2);

            // 첫 번째 환아 검증
            UnregisteredPatientResponse first = results.get(0);
            assertThat(first.childName()).isEqualTo("박튼튼");
            assertThat(first.parentPhone()).isEqualTo("01012345678");
            assertThat(first.childMonths()).isEqualTo(14); // 2024-11-20 ~ 2026-01-20 = 14개월
            assertThat(first.status()).isEqualTo("ISSUED");
            assertThat(first.scheduledAt()).isEqualTo(LocalDateTime.of(2026, 1, 20, 10, 0));

            // 두 번째 환아 검증
            UnregisteredPatientResponse second = results.get(1);
            assertThat(second.childName()).isEqualTo("김건강");
            assertThat(second.childMonths()).isEqualTo(19); // 2024-06-15 ~ 2026-01-20 = 19개월

            verify(inviteCodeRepository, times(1))
                    .findUnregisteredPatientsByHospitalAndDate(hospitalId, targetDate);
        }

        @Test
        @DisplayName("성공: 조회 결과가 없으면 빈 리스트를 반환한다")
        void getUnregisteredPatients_EmptyResult() {
            // given
            UUID hospitalId = testHospital.getHospitalId();
            int year = 2026;
            int month = 12;
            int day = 31;
            LocalDate targetDate = LocalDate.of(year, month, day);

            given(inviteCodeRepository.findUnregisteredPatientsByHospitalAndDate(hospitalId, targetDate))
                    .willReturn(List.of());

            // when
            List<UnregisteredPatientResponse> results = inviteCodeService
                    .getUnregisteredPatients(hospitalId, year, month, day);

            // then
            assertThat(results).isEmpty();
            verify(inviteCodeRepository, times(1))
                    .findUnregisteredPatientsByHospitalAndDate(hospitalId, targetDate);
        }

        @Test
        @DisplayName("성공: 개월 수 계산이 정확하다")
        void getUnregisteredPatients_CorrectMonthsCalculation() {
            // given
            UUID hospitalId = testHospital.getHospitalId();
            LocalDate targetDate = LocalDate.of(2026, 1, 30); // 현재 날짜로 가정

            // 생년월일이 정확히 1년 전 (12개월)
            InviteCode exactOneYear = InviteCode.builder()
                    .inviteCode("FTL-TEST-01")
                    .hospitalStaff(deskStaff)
                    .childName("정확1년")
                    .childBirthdate(LocalDate.of(2025, 1, 30))
                    .parentPhone("01011111111")
                    .scheduledAt(LocalDateTime.of(2026, 1, 30, 10, 0))
                    .inviteCodeStatus(InviteCodeStatus.ISSUED)
                    .build();
            ReflectionTestUtils.setField(exactOneYear, "inviteCodeId", UUID.randomUUID());

            // 생년월일이 2개월 1일 전 (2개월로 계산되어야 함)
            InviteCode twoMonthsOld = InviteCode.builder()
                    .inviteCode("FTL-TEST-02")
                    .hospitalStaff(deskStaff)
                    .childName("두달아기")
                    .childBirthdate(LocalDate.of(2025, 11, 29))
                    .parentPhone("01022222222")
                    .scheduledAt(LocalDateTime.of(2026, 1, 30, 14, 0))
                    .inviteCodeStatus(InviteCodeStatus.ISSUED)
                    .build();
            ReflectionTestUtils.setField(twoMonthsOld, "inviteCodeId", UUID.randomUUID());

            given(inviteCodeRepository.findUnregisteredPatientsByHospitalAndDate(hospitalId, targetDate))
                    .willReturn(List.of(exactOneYear, twoMonthsOld));

            // when
            List<UnregisteredPatientResponse> results = inviteCodeService
                    .getUnregisteredPatients(hospitalId, 2026, 1, 30);

            // then
            assertThat(results).hasSize(2);
            assertThat(results.get(0).childMonths()).isEqualTo(12);
            assertThat(results.get(1).childMonths()).isEqualTo(2);
        }
    }

}