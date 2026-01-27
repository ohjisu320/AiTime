package com.ssafy.aitime.domain.child.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.request.ChildDeleteResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildInfoResponse;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.exception.ChildAccessDeniedException;
import com.ssafy.aitime.domain.child.exception.ChildNotFoundException;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
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

    private long getChildMonths(LocalDate birthdate){
        return ChronoUnit.MONTHS.between(birthdate, LocalDate.now());
    }
}
