package com.ssafy.aitime.domain.child.service;

import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.response.ChildCreateResponse;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ChildServiceImpl implements ChildService{

    private final ChildRepository childRepository;

    private final UserService userService;

    @Override
    @Transactional
    public ChildCreateResponse addChild(UUID userId, ChildCreateRequest request) {
        User user = userService.getById(userId);

        Child child = Child.builder()
                .user(user)
                .name(request.name())
                .birthdate(request.birthdate())
                .gender(request.gender())
                .build();

        Child savedChild = childRepository.save(child);

        long months = getChildMonths(savedChild.getBirthdate());

        return new ChildCreateResponse(
                savedChild.getChildId(),
                savedChild.getName(),
                months,
                savedChild.getGender());
    }

    private long getChildMonths(LocalDate birthdate){
        return ChronoUnit.MONTHS.between(birthdate, LocalDate.now());
    }
}
