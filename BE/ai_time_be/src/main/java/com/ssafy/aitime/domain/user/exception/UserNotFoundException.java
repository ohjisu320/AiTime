package com.ssafy.aitime.domain.user.exception;

public class UserNotFoundException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public UserNotFoundException() {
        super("존재하지 않는 유저입니다.");
    }
}
