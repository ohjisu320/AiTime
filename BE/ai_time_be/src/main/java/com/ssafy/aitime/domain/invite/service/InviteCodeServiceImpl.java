package com.ssafy.aitime.domain.invite.service;

import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.exception.HospitalStaffAccessDeniedException;
import com.ssafy.aitime.domain.hospital.exception.InvalidDoctorSelectionException;
import com.ssafy.aitime.domain.hospital.service.HospitalStaffService;
import com.ssafy.aitime.domain.invite.dto.request.InviteCodeRequest;
import com.ssafy.aitime.domain.invite.dto.response.*;
import com.ssafy.aitime.domain.invite.entity.InviteCode;
import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import com.ssafy.aitime.domain.invite.exception.AlreadyIssuedInviteCodeException;
import com.ssafy.aitime.domain.invite.exception.InviteCodeAlreadyUsedException;
import com.ssafy.aitime.domain.invite.exception.InviteCodeNotFoundException;
import com.ssafy.aitime.domain.invite.repository.InviteCodeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class InviteCodeServiceImpl implements InviteCodeService {

    private final InviteCodeRepository inviteCodeRepository;

    private final HospitalStaffService hospitalStaffService;

    private static final String ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    private static final SecureRandom RANDOM = new SecureRandom();

    @Override
    @Transactional(readOnly = true)
    public InviteCodeValidationResponse validateAndGetInviteCode(String inviteCode) {
        // 1. 초대 코드 조회
        InviteCode codeEntity = inviteCodeRepository.findByInviteCode(inviteCode)
                .orElseThrow(InviteCodeNotFoundException::new);

        // 2. 이미 사용된 코드인지 확인 (만료 체크 제거)
        if (codeEntity.isAlreadyUsed()) {
            throw new InviteCodeAlreadyUsedException();
        }

        // 3. 필요한 정보만 DTO로 변환하여 반환
        return InviteCodeValidationResponse.from(
                codeEntity.getInviteCode(),
                codeEntity.getHospitalStaff().getHospital(),
                codeEntity.getScheduledAt(),
                codeEntity.getDoctorId()
        );
    }

    @Override
    @Transactional
    public void markAsUsed(String inviteCode) {
        // 초대 코드 조회
        InviteCode codeEntity = inviteCodeRepository.findByInviteCode(inviteCode)
                .orElseThrow(InviteCodeNotFoundException::new);

        // 사용 처리
        codeEntity.markAsUsed();
        inviteCodeRepository.save(codeEntity);
    }

    @Override
    @Transactional
    public InviteCodeResponse generateInviteCode(InviteCodeRequest request, UUID hospitalStaffId) {
// 1. 서비스 간 의존을 통해 발급자(Staff) 엔티티 조회
        HospitalStaff staff = hospitalStaffService.getHospitalStaffById(hospitalStaffId);

        // 2. 비즈니스 권한 체크: DESK 역할만 가능
        if (staff.getStaffRole() != StaffRole.DESK) {
            throw new HospitalStaffAccessDeniedException();
        }

        if (request.doctorId() != null) {
            HospitalStaff doctor = hospitalStaffService.getHospitalStaffById(request.doctorId());

            // 의사 역할인지 + 같은 병원 소속인지 검증
            if (doctor.getStaffRole() != StaffRole.DOCTOR ||
                    !doctor.getHospital().getHospitalId().equals(staff.getHospital().getHospitalId())) {
                throw new InvalidDoctorSelectionException(); // 커스텀 예외 권장
            }
        }

        // 중복 발급 확인: "같은 의사"에게 이미 발급된 ISSUED 코드가 있는지 확인
        inviteCodeRepository.findByChildNameAndChildBirthdateAndParentPhoneAndInviteCodeStatusAndDoctorId(
                request.childName(),
                request.childBirthdate(),
                request.parentPhone(),
                InviteCodeStatus.ISSUED,
                request.doctorId() // doctorId가 null인 경우 '의사 미지정' 코드를 검색함
        ).ifPresent(existing -> {
            throw new AlreadyIssuedInviteCodeException();
        });

        // 3. 고유한 비즈니스 코드 생성 (FTL-XXXX-XX)
        String businessCode;
        do {
            businessCode = createRandomCode();
        } while (inviteCodeRepository.existsByInviteCode(businessCode));

        // 4. 엔티티 생성 및 저장
        InviteCode inviteCode = InviteCode.builder()
                .inviteCode(businessCode)
                .hospitalStaff(staff)
                .childName(request.childName())
                .childBirthdate(request.childBirthdate())
                .parentPhone(request.parentPhone())
                .scheduledAt(request.scheduledAt())
                .doctorId(request.doctorId())
                .build();

        InviteCode saved = inviteCodeRepository.save(inviteCode);

        return new InviteCodeResponse(
                saved.getInviteCodeId(),
                saved.getInviteCode(),
                saved.getChildName(),
                saved.getParentPhone(),
                saved.getInviteCodeStatus(),
                saved.getCreatedAt()
        );
    }

    @Override
    @Transactional
    public InviteCodeRevokeResponse revokeInviteCode(UUID inviteCodeId, UUID hospitalStaffId) {
        // 1. 발급자(Staff) 권한 체크
        HospitalStaff staff = hospitalStaffService.getHospitalStaffById(hospitalStaffId);
        if (staff.getStaffRole() != StaffRole.DESK) {
            throw new HospitalStaffAccessDeniedException();
        }

        // 2. 초대코드 존재 여부 확인
        InviteCode inviteCode = inviteCodeRepository.findById(inviteCodeId)
                .orElseThrow(InviteCodeNotFoundException::new);

        if (!inviteCode.getHospitalStaff().getHospitalStaffId().equals(hospitalStaffId)) {
            throw new HospitalStaffAccessDeniedException();
        }

        // 3. 이미 사용된 코드인지 확인 (사용된 코드는 취소 불가)
        if (inviteCode.isAlreadyUsed()) {
            throw new InviteCodeAlreadyUsedException();
        }

        // 4. 상태 변경 (REVOKED)
        inviteCode.updateStatus(InviteCodeStatus.REVOKED);

        // Dirty Checking으로 자동 업데이트되지만, 명확성을 위해 save 호출 가능
        InviteCode updated = inviteCodeRepository.save(inviteCode);

        return new InviteCodeRevokeResponse(
                updated.getInviteCodeId(),
                updated.getInviteCodeStatus(),
                updated.getUpdatedAt()
        );
    }

    @Override
    @Transactional(readOnly = true)
    public InviteCodeStatusResponse getInviteCodeStatus(UUID inviteCodeId) {
// 1. 초대코드 엔티티 조회
        InviteCode inviteCode = inviteCodeRepository.findById(inviteCodeId)
                .orElseThrow(InviteCodeNotFoundException::new);

        // 2. DTO 변환 및 반환
        return new InviteCodeStatusResponse(
                inviteCode.getInviteCodeId(),
                inviteCode.getInviteCodeStatus(),
                inviteCode.getChildName()
        );
    }

    @Override
    public List<UnregisteredPatientResponse> getUnregisteredPatients(UUID hospitalId, int year, int month, int day) {
        // 1. 날짜 생성
        LocalDate targetDate = LocalDate.of(year, month, day);

        // 2. 해당 병원의 해당 날짜 미등록 환아 조회
        List<InviteCode> inviteCodes = inviteCodeRepository
                .findUnregisteredPatientsByHospitalAndDate(hospitalId, targetDate);

        // 3. DTO 변환 및 반환
        return inviteCodes.stream()
                .map(UnregisteredPatientResponse::from)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public List<LocalDate> getScheduledDates(UUID hospitalId, int year, int month) {
        // 1. 해당 월의 시작과 끝 계산
        LocalDate firstDayOfMonth = LocalDate.of(year, month, 1);
        LocalDateTime startOfMonth = firstDayOfMonth.atStartOfDay();
        LocalDateTime endOfMonth = firstDayOfMonth.plusMonths(1).atStartOfDay();

        // 2. 해당 병원의 해당 월 초대코드 조회
        List<InviteCode> inviteCodes = inviteCodeRepository
                .findIssuedInviteCodesByHospitalAndMonth(hospitalId, startOfMonth, endOfMonth);

        // 3. scheduledAt에서 날짜만 추출하고 중복 제거 후 정렬
        return inviteCodes.stream()
                .map(ic -> ic.getScheduledAt().toLocalDate())
                .distinct()
                .sorted()
                .toList();
    }

    private String createRandomCode() {
        StringBuilder sb = new StringBuilder("FTL-");
        for (int i = 0; i < 4; i++) {
            sb.append(ALPHABET.charAt(RANDOM.nextInt(ALPHABET.length())));
        }
        sb.append("-");
        for (int i = 0; i < 2; i++) {
            sb.append(RANDOM.nextInt(10));
        }
        return sb.toString();
    }
}
