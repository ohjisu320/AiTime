package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.dto.request.PresignedUrlRequest;
import com.ssafy.aitime.domain.exam.dto.response.PresignedUrlResponse;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import com.ssafy.aitime.domain.exam.exception.*;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.PresignedPutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class VideoServiceImpl implements VideoService {

    private final VideoRepository videoRepository;
    private final ExamRepository examRepository;
    private final S3Presigner s3Presigner;

    @Value("${minio.bucket-name}")
    private String bucketName;

    @Value("${minio.max-file-size}")
    private long maxFileSize;

    @Value("${minio.url-expiration-minutes}")
    private int urlExpirationMinutes;

    @Override
    @Transactional
    public PresignedUrlResponse generatePresignedUploadUrl(UUID examId, PresignedUrlRequest request) {

        // 1. Exam 조회 및 검증
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new ExamNotFoundException(examId));

        // TODO: 검사 상태 검증 (exam.getStatus()가 UPLOADING 가능한 상태인지 확인)
         if (exam.getExamStatus() != ExamStatus.IN_PROGRESS) {
             throw new ExamStatusNotAllowedException("이미 완료된 검사입니다");
         }

        // 2. VideoType 검증
        VideoType videoType;
        try {
            videoType = VideoType.valueOf(request.videoType());
        } catch (IllegalArgumentException e) {
            throw new InvalidVideoTypeException(request.videoType());
        }

        // 3. 파일 크기 검증
        if (request.contentLength() != null && request.contentLength() > maxFileSize) {
            throw new FileSizeLimitExceededException(maxFileSize);
        }

        // 4. 기존 Video 조회 또는 생성
        Optional<Video> existingVideo = videoRepository.findByExamExamIdAndVideoType(examId, videoType);

        Video video;
        if (existingVideo.isPresent()) {
            video = existingVideo.get();
            log.info("기존 Video 재사용: videoId={}, videoType={}", video.getVideoId(), videoType);
        } else {
            // S3 키 생성
            String videoUuid = UUID.randomUUID().toString();
            String s3Url = String.format("exams/%s/%s/%s.mp4",
                    examId,
                    videoType.name(),
                    videoUuid.substring(0, 13)); // UUID 일부만 사용

            // 새 Video 엔티티 생성 (PENDING_UPLOAD 상태)
            video = Video.builder()
                    .exam(exam)
                    .videoType(videoType)
                    .s3Bucket(bucketName)
                    .s3Url(s3Url)
                    .videoStatus(VideoStatus.PENDING_UPLOAD)
                    .build();

            video = videoRepository.save(video);
            log.info("새 Video 생성: videoId={}, s3Url={}", video.getVideoId(), s3Url);
        }

        // 5. Presigned URL 생성
        try {
            PutObjectRequest.Builder putRequestBuilder = PutObjectRequest.builder()
                    .bucket(bucketName)
                    .key(video.getS3Url());

            // contentType이 제공된 경우 서명에 포함
            if (request.contentType() != null) {
                putRequestBuilder.contentType(request.contentType());
            }

            PutObjectRequest putObjectRequest = putRequestBuilder.build();

            Duration expiration = Duration.ofMinutes(urlExpirationMinutes);
            PutObjectPresignRequest presignRequest = PutObjectPresignRequest.builder()
                    .signatureDuration(expiration)
                    .putObjectRequest(putObjectRequest)
                    .build();

            PresignedPutObjectRequest presignedRequest = s3Presigner.presignPutObject(presignRequest);
            String presignedUrl = presignedRequest.url().toString();
            LocalDateTime expiresAt = LocalDateTime.now().plusMinutes(urlExpirationMinutes);

            log.info("Presigned URL 생성 완료: videoId={}, expiresAt={}", video.getVideoId(), expiresAt);

            // 6. 응답 생성
            Map<String, String> requiredHeaders = Map.of(
                    "Content-Type", request.contentType()
            );

            return PresignedUrlResponse.builder()
                    .videoId(video.getVideoId().toString())
                    .examId(examId.toString())
                    .videoType(videoType.name())
                    .bucket(bucketName)
                    .s3Key(video.getS3Url())
                    .uploadUrl(presignedUrl)
                    .requiredHeaders(requiredHeaders)
                    .expiresAt(expiresAt)
                    .build();

        } catch (Exception e) {
            log.error("Presigned URL 생성 실패: videoId={}", video.getVideoId(), e);
            throw new S3UploadException(e);
        }
    }
}