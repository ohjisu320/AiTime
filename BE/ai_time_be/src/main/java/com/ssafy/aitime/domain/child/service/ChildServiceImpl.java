package com.ssafy.aitime.domain.child.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.request.ChildDeleteResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildHomeResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildHospitalListResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildInfoResponse;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalInfoDTO;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.exception.ChildAccessDeniedException;
import com.ssafy.aitime.domain.child.exception.ChildNotFoundException;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.dto.response.ExamSummaryResponse;
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
import java.time.LocalDateTime;
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

    @Override
    @Transactional(readOnly = true)
    public ChildHomeResponse getChildHomeInfo(UUID userId, UUID childId) {
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

        // 아이 홈 정보 조회 수행
        // - ExamService를 통해 검사 정보 가져오기(isExamEligible, hasPreviousExam, hasPreviousExam, nextEligibleAt)
        ExamSummaryResponse examSummary = examService.getExamSummaryForChild(childId)
                .orElseGet(() -> new ExamSummaryResponse(false, 0, false, LocalDateTime.now()));
        // - HospitalService를 통해 병원 정보 가져오기(linkedHospitals)
        List<HospitalInfoDTO> linkedHospitals = hospitalService.getLinkedHospitalsByChild(childId);

        // 4. DTO 조립 및 반환
        return new ChildHomeResponse(
                child.getChildId(),
                child.getName(),
                child.getGender(),
                examSummary.isExamEligible(), // record 필드명이 isExamEligible이면 맞음
                examSummary.examProgress(),   // examProgress() 로 호출
                examSummary.hasPreviousExam(),// hasPreviousExam() 로 호출
                examSummary.nextEligibleAt().toLocalDate(), // nextEligibleAt() 로 호출
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

}
