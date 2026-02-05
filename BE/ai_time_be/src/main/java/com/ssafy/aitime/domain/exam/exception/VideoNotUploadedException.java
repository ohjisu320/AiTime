package com.ssafy.aitime.domain.exam.exception;

import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;

/**
 * 비디오가 아직 업로드 완료되지 않아 조회할 수 없는 상태일 때 발생하는 예외
 * HTTP 409 Conflict
 */
public class VideoNotUploadedException extends RuntimeException {
    public VideoNotUploadedException(VideoStatus currentStatus) {
        super(String.format("영상이 아직 업로드 완료되지 않았습니다. 현재 상태: %s", currentStatus));
    }
}