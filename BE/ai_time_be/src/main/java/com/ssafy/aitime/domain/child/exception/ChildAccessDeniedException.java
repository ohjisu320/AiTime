package com.ssafy.aitime.domain.child.exception;

public class ChildAccessDeniedException extends RuntimeException {
	private static final long serialVersionUID = 1L;

	public ChildAccessDeniedException() {
        super("해당 아이 정보에 대한 접근 권한이 없습니다.");
    }
}
