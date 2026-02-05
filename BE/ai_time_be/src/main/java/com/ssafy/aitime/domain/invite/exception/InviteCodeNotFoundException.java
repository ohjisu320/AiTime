package com.ssafy.aitime.domain.invite.exception;

public class InviteCodeNotFoundException extends RuntimeException {

    public InviteCodeNotFoundException() {
        super("유효하지 않은 초대 코드입니다.");
    }
}