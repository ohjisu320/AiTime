package com.ssafy.aitime.domain.invite.exception;

public class AlreadyIssuedInviteCodeException extends RuntimeException {

    public AlreadyIssuedInviteCodeException() {
        super("해당 환아에게 이미 발급된 유효한 초대 코드가 존재합니다.");
    }
}
