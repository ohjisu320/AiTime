package com.ssafy.aitime.domain.invite.exception;

public class InviteCodeAlreadyUsedException extends RuntimeException {

    public InviteCodeAlreadyUsedException() {
        super("이미 사용된 초대 코드입니다.");
    }
}