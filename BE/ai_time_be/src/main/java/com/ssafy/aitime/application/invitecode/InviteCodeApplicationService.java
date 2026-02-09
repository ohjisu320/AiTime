package com.ssafy.aitime.application.invitecode;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.exception.ChildAccessDeniedException;
import com.ssafy.aitime.domain.child.exception.ChildNotFoundException;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.hospital.dto.request.ReservationCreateRequest;
import com.ssafy.aitime.domain.hospital.service.HospitalService;
import com.ssafy.aitime.domain.hospital.service.ReservationService;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeValidationResponse;
import com.ssafy.aitime.domain.invite.service.InviteCodeService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

/**
 * 초대 코드 등록 유즈케이스를 처리하는 Application Service
 * 여러 도메인(Child, Hospital, InviteCode, Reservation)을 조율
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class InviteCodeApplicationService {

    private final ChildRepository childRepository;
    private final InviteCodeService inviteCodeService;
    private final HospitalService hospitalService;
    private final ReservationService reservationService;

    @Transactional
    public void registerInviteCode(UUID childId, String inviteCode, UUID userId) {
        log.info("Processing invite code registration - childId: {}, userId: {}", childId, userId);

        // 1. 초대 코드 검증
        InviteCodeValidationResponse validatedCode =
                inviteCodeService.validateAndGetInviteCode(inviteCode);

        // 2. 자녀 소유권 확인
        Child child = childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE)
                .orElseThrow(ChildNotFoundException::new);

        if (!child.getUser().getUserId().equals(userId)) {
            throw new ChildAccessDeniedException();
        }

        // 3. 병원-자녀 연동
        UUID hospitalChildrenId = hospitalService.linkChildToHospital(
                childId,
                validatedCode.hospitalId()
        );

        // 4. 초대 코드 사용 처리
        inviteCodeService.markAsUsed(inviteCode);

        // 5. 예약 생성
        ReservationCreateRequest reservationRequest = ReservationCreateRequest.builder()
                .hospitalChildrenId(hospitalChildrenId)
                .scheduledAt(validatedCode.scheduledAt())
                .doctorId(validatedCode.doctorId())
                .build();

        reservationService.insertReservation(reservationRequest);

        log.info("Invite code registration completed - childId: {}", childId);
    }
}
