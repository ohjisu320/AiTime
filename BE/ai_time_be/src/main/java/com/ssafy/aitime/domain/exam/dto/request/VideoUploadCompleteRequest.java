package com.ssafy.aitime.domain.exam.dto.request;

import jakarta.validation.constraints.NotNull;

/**
 * 영상 업로드 완료 요청 DTO
 * 프론트엔드가 Presigned URL로 영상을 S3에 직접 업로드한 후,
 * 백엔드에 업로드 완료를 알리기 위한 요청
 */
public record VideoUploadCompleteRequest(

        /**
         * S3 업로드에 사용한 s3Key (검증용)
         * 예: "exams/3fa85f64-5717-4562-b3fc-2c963f66afa6/POSE_IMITATION/abc123def.mp4"
         */
        @NotNull(message = "s3Key는 필수입니다")
        String s3Key
) {
}