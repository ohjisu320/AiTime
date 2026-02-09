package com.ssafy.aitime.domain.child.exception;

public class ChildNotFoundException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public ChildNotFoundException() {
        super("존재하지 않는 아이 정보 입니다.");
    }
}
