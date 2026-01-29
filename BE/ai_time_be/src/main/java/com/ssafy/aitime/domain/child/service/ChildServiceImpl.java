package com.ssafy.aitime.domain.child.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.request.ChildDeleteResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildHomeResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildHospitalListResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildInfoResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamStartResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryDTO;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalInfoDTO;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.exception.ChildAccessDeniedException;
import com.ssafy.aitime.domain.child.exception.ChildNotFoundException;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.service.ExamService;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalResponseDto;
import com.ssafy.aitime.domain.hospital.service.HospitalChildrenService;
import com.ssafy.aitime.domain.hospital.service.HospitalService;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeValidationDto;
import com.ssafy.aitime.domain.invite.service.InviteCodeService;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ChildServiceImpl implements ChildService{

    private final ChildRepository childRepository;

    private final UserService userService;
    private final ExamService examService;
    private final HospitalService hospitalService;
    private final InviteCodeService inviteCodeService;
    private final HospitalChildrenService hospitalChildrenService;

    @Override
    @Transactional
    public ChildInfoResponse addChild(UUID userId, ChildCreateRequest request) {
        User user = userService.getById(userId);

        Child child = Child.builder()
                .user(user)
                .name(request.name())
                .birthdate(request.birthdate())
                .gender(request.gender())
                .build();

        Child savedChild = childRepository.save(child);

        long months = getChildMonths(savedChild.getBirthdate());

        return new ChildInfoResponse(
                savedChild.getChildId(),
                savedChild.getName(),
                months,
                savedChild.getGender());
    }

    @Override
    @Transactional(readOnly = true)
    public List<ChildInfoResponse> getChildList(UUID userId) {

        User user = userService.getById(userId);

        return childRepository.findByUser_UserIdAndRecordStatus(user.getUserId(), RecordStatus.ACTIVE)
                .stream()
                .map(child -> new ChildInfoResponse(
                        child.getChildId(),
                        child.getName(),
                        getChildMonths(child.getBirthdate()), // 기존 로직 재사용
                        child.getGender()
                ))
                .toList();
    }

    @Override
    @Transactional
    public ChildDeleteResponse deleteChild(UUID userId, UUID childId) {
        // 삭제 주체(부모)가 유효한지 확인
        userService.getById(userId);

        // 삭제할 아이가 존재하는지 확인 (ACTIVE 상태만)
        Child child = childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE)
                .orElseThrow(ChildNotFoundException::new);

        // 권한 체크: 아이의 부모 ID와 현재 로그인한 유저 ID 비교
        if (!child.getUser().getUserId().equals(userId)) {
            // 본인의 아이가 아니면 에러 발생
            throw new ChildAccessDeniedException();
        }

        // 삭제 수행 (Soft Delete)
        childRepository.delete(child);

        return new ChildDeleteResponse(childId, RecordStatus.DELETED);
    }

    /**
     * 아이 홈 정보 조회 - API 명세서에 맞게 수정
     * ExamService에서 검사 상태를 계산한 DTO를 받아서 조립
     */
    @Override
    @Transactional(readOnly = true)
    public ChildHomeResponse getChildHomeInfo(UUID userId, UUID childId) {
        // 1. 권한 검증
        userService.getById(userId);
        Child child = childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE)
                .orElseThrow(ChildNotFoundException::new);

        if (!child.getUser().getUserId().equals(userId)) {
            throw new ChildAccessDeniedException();
        }

        // 2. ExamService에서 검사 요약 정보 조회 (상태 계산 포함)
        ExamSummaryDTO examSummary = examService.getExamSummaryForChild(childId);

        // 3. HospitalService에서 연동된 병원 목록 조회
        List<HospitalInfoDTO> linkedHospitals = hospitalService.getLinkedHospitalsByChild(childId);

        // 4. DTO 조립 및 반환
        return new ChildHomeResponse(
                child.getChildId(),
                child.getName(),
                child.getGender(),
                examSummary.childHomeStatus(),
                examSummary.examProgress(),
                examSummary.examStartedAt(),
                examSummary.nextEligibleAt(),
                examSummary.draftExpiresAt(),
                linkedHospitals
        );
    }

    private long getChildMonths(LocalDate birthdate){
        return ChronoUnit.MONTHS.between(birthdate, LocalDate.now());
    }

    @Override
    @Transactional
    public void registerInviteCode(UUID childId, String inviteCode, UUID userId) {
        // 1. 초대 코드 검증 (InviteCodeService에서 DTO로 반환)
        InviteCodeValidationDto validatedCode = inviteCodeService.validateAndGetInviteCode(inviteCode);

        // 2. 자녀 소유권 확인 (현재 로그인한 부모의 자녀가 맞는지)
        Child child = childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE)
                .orElseThrow(ChildNotFoundException::new);

        if (!child.getUser().getUserId().equals(userId)) {
            throw new ChildAccessDeniedException();
        }

        // 3. 병원-자녀 연동 (HospitalService에 위임)
        hospitalService.linkChildToHospital(childId, validatedCode.getHospitalId());

        // 4. 초대 코드 사용 처리 (InviteCodeService에서 처리)
        inviteCodeService.markAsUsed(inviteCode);
    }

    @Override
    @Transactional(readOnly = true)
    public ChildHospitalListResponse getLinkedHospitals(UUID userId, UUID childId) {
        // 아이 주체(부모)가 유효한지 확인
        userService.getById(userId);

        // 조회할 아이가 존재하는지 확인 (ACTIVE 상태만)
        Child child = childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE)
                .orElseThrow(ChildNotFoundException::new);

        // 권한 체크: 아이의 부모 ID와 현재 로그인한 유저 ID 비교
        if (!child.getUser().getUserId().equals(userId)) {
            // 본인의 아이가 아니면 에러 발생
            throw new ChildAccessDeniedException();
        }

        // 연동된 병원 리스트 조회
        List<HospitalResponseDto> hospitalResponseDtoList = hospitalChildrenService.getHospitalResponseDtosByChild(childId);

        return new ChildHospitalListResponse(hospitalResponseDtoList);
    }

    @Override
    @Transactional
    public ExamStartResponse childStartExam(UUID userId, UUID childId, Boolean videoConsent) {
        // 1. videoConsent 확인
        if (videoConsent == null || !videoConsent) {
            throw new IllegalArgumentException("비디오 동의가 필요합니다");
        }

        // 2. Child 조회
        Child child = childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE)
                .orElseThrow(() -> new ChildNotFoundException());

        // 3. 권한 확인
        if (!child.getUser().getUserId().equals(userId)) {
            throw new ChildAccessDeniedException();
        }

        // 4. ExamService에 Child 엔티티 전달하여 검사 생성
        return examService.createExam(child);
    }

}
