package com.ssafy.aitime.domain.exam.dto.response;

import lombok.Builder;

/**
 * 영상 업로드 완료 응답 DTO
 */
@Builder
public record VideoUploadCompleteResponse(

        /**
         * 비디오 ID
         */
        String videoId,

        /**
         * 검사 ID
         */
        String examId,

        /**
         * 비디오 상태 (UPLOADED)
         */
        String status,

        /**
         * 검증 완료 여부
         */
        Boolean verified
) {}