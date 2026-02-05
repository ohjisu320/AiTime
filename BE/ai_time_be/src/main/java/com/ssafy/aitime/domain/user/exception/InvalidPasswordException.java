package com.ssafy.aitime.domain.user.exception;

public class InvalidPasswordException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public InvalidPasswordException() {
        super("비밀번호가 올바르지 않습니다.");
    }

    public InvalidPasswordException(String message) {
        super(message);
    }
}
