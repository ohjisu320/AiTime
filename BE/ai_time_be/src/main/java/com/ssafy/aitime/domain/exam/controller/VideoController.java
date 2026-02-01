package com.ssafy.aitime.domain.exam.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.exam.dto.request.PresignedKeyRequest;
import com.ssafy.aitime.domain.exam.dto.request.VideoUploadCompleteRequest;
import com.ssafy.aitime.domain.exam.dto.response.PresignedKeyResponse;
import com.ssafy.aitime.domain.exam.dto.response.VideoUploadCompleteResponse;
import com.ssafy.aitime.domain.exam.service.VideoService;
import com.ssafy.aitime.security.principal.UserPrincipal;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
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
    public ResponseEntity<ApiResponse<PresignedKeyResponse>> generatePresignedUploadUrl(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable("examId") UUID examId,
            @Valid @RequestBody PresignedKeyRequest request) {

        log.info("Presigned URL 요청: userId={}, examId={}, videoType={}",
                principal.getUserId(), examId, request.videoType());

        return ResponseEntity.ok(
                ApiResponse.ok("업로드 URL이 발급되었습니다.",
                        videoService.generatePresignedUploadKey(principal.getUserId(), examId, request))
        );
    }

    @Operation(
            summary = "영상 업로드 완료 통지",
            description = "프론트엔드가 Presigned URL을 사용하여 영상을 S3에 직접 업로드한 후, " +
                    "서버에 업로드 완료를 알리고 Video 엔티티의 상태를 UPLOADED로 변경합니다. " +
                    "이 API는 S3에 파일이 실제로 존재하는지 HEAD 요청으로 검증합니다."
    )
    @PostMapping("/{examId}/videos/{videoId}/complete")
    public ResponseEntity<ApiResponse<VideoUploadCompleteResponse>> completeVideoUpload(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable("examId") UUID examId,
            @PathVariable("videoId") UUID videoId,
            @Valid @RequestBody VideoUploadCompleteRequest request) {

        log.info("영상 업로드 완료 요청: userId={}, examId={}, videoId={}, s3Url={}",
                principal.getUserId(), examId, videoId, request.s3Key());

        return ResponseEntity.ok(
                ApiResponse.ok("영상 업로드가 확인되었습니다.",
                        videoService.completeVideoUpload(principal.getUserId(), examId, videoId, request))
        );
    }
}