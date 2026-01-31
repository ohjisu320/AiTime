package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.dto.request.PresignedKeyRequest;
import com.ssafy.aitime.domain.exam.dto.request.VideoUploadCompleteRequest;
import com.ssafy.aitime.domain.exam.dto.response.PresignedKeyResponse;
import com.ssafy.aitime.domain.exam.dto.response.VideoUploadCompleteResponse;
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
import software.amazon.awssdk.services.s3.S3Client;
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
    private final S3Client s3Client;  // S3 파일 검증을 위해 추가


    @Value("${minio.bucket-name}")
    private String bucketName;

    @Value("${minio.max-file-size}")
    private long maxFileSize;

    @Value("${minio.key-expiration-minutes}")
    private int KeyExpirationMinutes;

    @Override
    @Transactional
    public PresignedKeyResponse generatePresignedUploadKey(UUID userId, UUID examId, PresignedKeyRequest request) {

        // 1. Exam 조회 및 검증
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new ExamNotFoundException(examId));

        // TODO: 검사 상태 검증 (exam.getStatus()가 UPLOADING 가능한 상태인지 확인)
         if (exam.getExamStatus() != ExamStatus.IN_PROGRESS) {
             throw new ExamStatusNotAllowedException("이미 완료된 검사입니다");
         }

        // 2. 권한 검증: Exam이 해당 User의 Child에 속하는지 확인
        if (!exam.getChild().getUser().getUserId().equals(userId)) {
            throw new ExamAccessDeniedException(examId);
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
            String s3Key = String.format("exams/%s/%s/%s.mp4",
                    examId,
                    videoType.name(),
                    videoUuid.substring(0, 13)); // UUID 일부만 사용

            // 새 Video 엔티티 생성 (PENDING_UPLOAD 상태)
            video = Video.builder()
                    .exam(exam)
                    .videoType(videoType)
                    .s3Bucket(bucketName)
                    .s3Key(s3Key)
                    .videoStatus(VideoStatus.PENDING_UPLOAD)
                    .build();

            video = videoRepository.save(video);
            log.info("새 Video 생성: videoId={}, s3Key={}", video.getVideoId(), s3Key);
        }

        // 5. Presigned Key 생성
        try {
            PutObjectRequest.Builder putRequestBuilder = PutObjectRequest.builder()
                    .bucket(bucketName)
                    .key(video.getS3Key());

            // contentType이 제공된 경우 서명에 포함
            if (request.contentType() != null) {
                putRequestBuilder.contentType(request.contentType());
            }

            PutObjectRequest putObjectRequest = putRequestBuilder.build();

            Duration expiration = Duration.ofMinutes(KeyExpirationMinutes);
            PutObjectPresignRequest presignRequest = PutObjectPresignRequest.builder()
                    .signatureDuration(expiration)
                    .putObjectRequest(putObjectRequest)
                    .build();

            PresignedPutObjectRequest presignedRequest = s3Presigner.presignPutObject(presignRequest);
            String presignedKey = presignedRequest.url().toString();
            LocalDateTime expiresAt = LocalDateTime.now().plusMinutes(KeyExpirationMinutes);

            log.info("Presigned Key 생성 완료: videoId={}, expiresAt={}", video.getVideoId(), expiresAt);

            // 6. 응답 생성
            Map<String, String> requiredHeaders = Map.of(
                    "Content-Type", request.contentType()
            );

            return PresignedKeyResponse.builder()
                    .videoId(video.getVideoId().toString())
                    .examId(examId.toString())
                    .videoType(videoType.name())
                    .bucket(bucketName)
                    .s3Key(video.getS3Key())
                    .uploadUrl(presignedKey)
                    .requiredHeaders(requiredHeaders)
                    .expiresAt(expiresAt)
                    .build();

        } catch (Exception e) {
            log.error("Presigned Key 생성 실패: videoId={}", video.getVideoId(), e);
            throw new S3UploadException(e);
        }
    }

    /**
     * 영상 업로드 완료 처리
     * 1. Video 조회 및 검증 (존재 여부, examId 일치 여부)
     * 2. S3 Key 검증 (요청의 s3Key와 Video의 s3Key 일치 여부)
     * 3. Video 상태 검증 (PENDING_UPLOAD 상태인지)
     * 4. S3 파일 존재 확인 (MinIO/S3에 실제 파일이 업로드되었는지)
     * 5. Video 상태를 UPLOADED로 변경
     */
    @Override
    @Transactional
    public VideoUploadCompleteResponse completeVideoUpload(UUID userId, UUID examId, UUID videoId, VideoUploadCompleteRequest request) {

        // 1. Video 조회 및 검증
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new VideoNotFoundException(videoId));

        // Video가 요청된 Exam에 속하는지 확인
        if (!video.getExam().getExamId().equals(examId)) {
            throw new VideoNotFoundException(videoId);
        }

        // 3. 권한 검증: Exam이 해당 User의 Child에 속하는지 확인
        if (!video.getExam().getChild().getUser().getUserId().equals(userId)) {
            throw new ExamAccessDeniedException(examId);
        }

        // 2. S3 Key 검증
        if (!video.getS3Key().equals(request.s3Key())) {
            log.error("S3 Key 불일치 - 예상: {}, 제공: {}", video.getS3Key(), request.s3Key());
            throw new S3KeyMismatchException(video.getS3Key(), request.s3Key());
        }

        // 3. Video 상태 검증
        if (video.getVideoStatus() != VideoStatus.PENDING_UPLOAD) {
            log.error("잘못된 비디오 상태 - videoId: {}, 현재 상태: {}", videoId, video.getVideoStatus());
            throw new InvalidVideoStatusException(video.getVideoStatus());
        }

        // 4. S3 파일 존재 확인
        boolean fileExists = verifyS3FileExists(video.getS3Bucket(), video.getS3Key());
        if (!fileExists) {
            log.error("S3 파일이 존재하지 않음 - bucket: {}, Key: {}", video.getS3Bucket(), video.getS3Key());
            throw new S3FileVerificationException(video.getS3Key());
        }

        // 5. Video 상태를 UPLOADED로 변경
        video.markUploaded();
        videoRepository.save(video);

        log.info("영상 업로드 완료 처리 성공 - videoId: {}, examId: {}, s3Key: {}",
                videoId, examId, request.s3Key());

        // 6. 응답 생성
        return VideoUploadCompleteResponse.of(
                video.getVideoId().toString(),
                video.getExam().getExamId().toString(),
                video.getVideoStatus().name(),
                true
        );
    }

    /**
     * S3(MinIO)에 파일이 실제로 존재하는지 확인
     * HEAD 요청을 통해 파일의 메타데이터만 조회하여 파일 존재 여부를 확인
     */
    private boolean verifyS3FileExists(String bucket, String s3Key) {
        try {
            s3Client.headObject(builder -> builder
                    .bucket(bucket)
                    .key(s3Key)
                    .build());
            return true;
        } catch (software.amazon.awssdk.services.s3.model.NoSuchKeyException e) {
            log.warn("S3 파일이 존재하지 않음 - bucket: {}, Key: {}", bucket, s3Key);
            return false;
        } catch (Exception e) {
            log.error("S3 파일 검증 중 오류 발생 - bucket: {}, Key: {}", bucket, s3Key, e);
            throw new S3FileVerificationException(s3Key, e);
        }
    }
}