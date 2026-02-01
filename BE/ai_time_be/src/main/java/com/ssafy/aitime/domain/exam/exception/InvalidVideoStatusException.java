package com.ssafy.aitime.domain.exam.exception;

import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;

/**
 * 비디오의 현재 상태가 업로드 완료 처리를 할 수 없는 상태일 때 발생하는 예외
 */
public class InvalidVideoStatusException extends RuntimeException {
    public InvalidVideoStatusException(VideoStatus currentStatus) {
        super(String.format("현재 비디오 상태(%s)에서는 업로드 완료 처리를 할 수 없습니다", currentStatus));
    }

    public InvalidVideoStatusException(String message) {
        super(message);
    }
}