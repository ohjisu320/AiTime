package com.ssafy.aitime.domain.invite.service;

import com.ssafy.aitime.domain.invite.dto.response.InviteCodeValidationDto;
import com.ssafy.aitime.domain.invite.entity.InviteCode;
import com.ssafy.aitime.domain.invite.exception.InviteCodeAlreadyUsedException;
import com.ssafy.aitime.domain.invite.exception.InviteCodeNotFoundException;
import com.ssafy.aitime.domain.invite.repository.InviteCodeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class InviteCodeServiceImpl implements InviteCodeService {
    private final InviteCodeRepository inviteCodeRepository;

    @Override
    @Transactional(readOnly = true)
    public InviteCodeValidationDto validateAndGetInviteCode(String inviteCode) {
        // 1. 초대 코드 조회
        InviteCode codeEntity = inviteCodeRepository.findByInviteCode(inviteCode)
                .orElseThrow(InviteCodeNotFoundException::new);

        // 2. 이미 사용된 코드인지 확인 (만료 체크 제거)
        if (codeEntity.isAlreadyUsed()) {
            throw new InviteCodeAlreadyUsedException();
        }

        // 3. 필요한 정보만 DTO로 변환하여 반환
        return InviteCodeValidationDto.from(
                codeEntity.getInviteCode(),
                codeEntity.getHospitalStaff().getHospital()
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
}
