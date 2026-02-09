package com.ssafy.aitime.domain.user.exception;

public class PhoneVerificationRequiredException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public PhoneVerificationRequiredException() {
        super("휴대폰 인증이 완료되지 않았습니다. 인증을 먼저 진행해주세요.");
    }

    public PhoneVerificationRequiredException(String message) {
        super(message);
    }
}
