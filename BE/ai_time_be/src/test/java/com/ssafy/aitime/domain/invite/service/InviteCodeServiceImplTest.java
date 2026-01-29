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
}