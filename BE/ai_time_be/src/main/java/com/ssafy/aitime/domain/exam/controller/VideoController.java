package com.ssafy.aitime.domain.exam.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.exam.dto.request.PresignedUrlRequest;
import com.ssafy.aitime.domain.exam.dto.response.PresignedUrlResponse;
import com.ssafy.aitime.domain.exam.service.VideoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/exam")
@RequiredArgsConstructor
@Tag(name = "Video", description = "영상 업로드 관련 API")
public class VideoController {

    private final VideoService videoService;

    @Operation(
            summary = "영상 업로드 Presigned URL 발급",
            description = "특정 검사(exam)에서 특정 태스크 영상 업로드를 위한 PUT Presigned URL을 발급하고, video 메타데이터를 UPLOADING 상태로 생성/갱신합니다."
    )
    @PostMapping("/{examId}/videos/presign-upload")
    public ResponseEntity<ApiResponse<PresignedUrlResponse>> generatePresignedUploadUrl(
            @PathVariable("examId") UUID examId,
            @Valid @RequestBody PresignedUrlRequest request) {

        log.info("Presigned URL 요청: examId={}, videoType={}", examId, request.videoType());

        PresignedUrlResponse response = videoService.generatePresignedUploadUrl(examId, request);

        return ResponseEntity.ok(
                ApiResponse.ok("업로드 URL이 발급되었습니다.", response)
        );
    }
}