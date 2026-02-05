package com.ssafy.aitime.domain.user.exception;

public class InvalidUserRoleException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public InvalidUserRoleException() {
        super("유효하지 않은 Role입니다.");
    }
}
