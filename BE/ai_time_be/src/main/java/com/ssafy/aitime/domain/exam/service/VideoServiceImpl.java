package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.dto.request.PresignedKeyRequest;
import com.ssafy.aitime.domain.exam.dto.request.VideoUploadCompleteRequest;
import com.ssafy.aitime.domain.exam.dto.response.PresignedKeyResponse;
import com.ssafy.aitime.domain.exam.dto.response.PresignedViewUrlResponse;
import com.ssafy.aitime.domain.exam.dto.response.VideoDeleteResponse;
import com.ssafy.aitime.domain.exam.dto.response.VideoUploadCompleteResponse;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import com.ssafy.aitime.domain.exam.exception.*;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import com.ssafy.aitime.domain.hospital.service.HospitalChildrenService;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import com.ssafy.aitime.security.principal.UserPrincipal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedGetObjectRequest;
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

    private final HospitalChildrenService hospitalChildrenService;
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
        return VideoUploadCompleteResponse
                .builder()
                .videoId(video.getVideoId().toString())
                .examId(video.getExam().getExamId().toString())
                .status(video.getVideoStatus().name())
                .verified(true)
                .build();
    }

    /**
     * S3(MinIO)에 파일이 실제로 존재하는지 확인
     * HEAD 요청을 통해 파일의 메타데이터만 조회하여 파일 존재 여부를 확인
     */
    public boolean verifyS3FileExists(String bucket, String s3Key) {
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

    @Override
    @Transactional(readOnly = true)
    public PresignedViewUrlResponse generatePresignedViewUrl(Object principal, UUID examId, UUID videoId, int expiresInSec) {

        // 1. Video 조회
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new VideoNotFoundException(videoId));

        // 2. Video가 요청된 Exam에 속하는지 확인
        if (!video.getExam().getExamId().equals(examId)) {
            log.error("Video가 해당 Exam에 속하지 않음 - videoId: {}, examId: {}, actualExamId: {}",
                    videoId, examId, video.getExam().getExamId());
            throw new VideoNotFoundException(videoId);
        }

        // 3. Principal 타입 검증 및 권한 확인
        validatePrincipalAndAuthorization(principal, examId);

        // 4. Video 상태 확인 - UPLOADED 상태만 조회 가능
        if (video.getVideoStatus() != VideoStatus.UPLOADED) {
            log.warn("업로드되지 않은 영상 조회 시도 - videoId: {}, status: {}",
                    video.getVideoId(), video.getVideoStatus());
            throw new VideoNotUploadedException(video.getVideoStatus());
        }

        // 5. url 생성 전 S3 파일 존재 확인
        boolean fileExists = verifyS3FileExists(video.getS3Bucket(), video.getS3Key());
        if (!fileExists) {
            log.error("S3 파일이 존재하지 않음 - bucket: {}, Key: {}", video.getS3Bucket(), video.getS3Key());
            throw new S3FileVerificationException(video.getS3Key());
        }

        // 7. Presigned GET URL 생성
        String presignedUrl = generatePresignedGetUrl(video.getS3Bucket(), video.getS3Key(), expiresInSec);
        LocalDateTime expiresAt = LocalDateTime.now().plusSeconds(expiresInSec);

        log.info("Presigned View URL 생성 완료 - videoId: {}, expiresAt: {}",
                video.getVideoId(), expiresAt);

        // 8. Response 생성
        return PresignedViewUrlResponse.builder()
            .examId(video.getExam().getExamId().toString())
            .videoId(video.getVideoId().toString())
            .bucket(video.getS3Bucket())
            .s3Key(video.getS3Key())
            .viewUrl(presignedUrl)
            .expiresAt(expiresAt)
            .build();
    }

    /**
     * Principal 타입에 따라 권한 검증
     * - UserPrincipal: 본인 또는 자녀의 exam인지 확인
     * - HospitalStaffPrincipal: 본인 병원과 연동된 아이의 exam인지 확인
     */
    private void validatePrincipalAndAuthorization(Object principal, UUID examId) {
        if (principal instanceof UserPrincipal userPrincipal) {
            validateUserAccess(userPrincipal, examId);
        } else if (principal instanceof HospitalStaffPrincipal staffPrincipal) {
            validateHospitalStaffAccess(staffPrincipal, examId);
        } else {
            log.error("지원하지 않는 Principal 타입: {}", principal.getClass().getName());
            throw new ExamAccessDeniedException(examId);
        }
    }

    /**
     * User 권한 검증: Exam이 User의 Child에 속하는지 확인
     */
    private void validateUserAccess(UserPrincipal userPrincipal, UUID examId) {
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new ExamNotFoundException(examId));

        UUID examUserId = exam.getChild().getUser().getUserId();
        UUID requestUserId = userPrincipal.getUserId();

        if (!examUserId.equals(requestUserId)) {
            log.warn("User 권한 없음 - userId: {}, examId: {}, examUserId: {}",
                    requestUserId, examId, examUserId);
            throw new ExamAccessDeniedException(examId);
        }

        log.debug("User 권한 검증 성공 - userId: {}, examId: {}", requestUserId, examId);
    }

    /**
     * HospitalStaff 권한 검증: Exam의 Child가 Staff의 Hospital과 연동되어 있는지 확인
     */
    private void validateHospitalStaffAccess(HospitalStaffPrincipal staffPrincipal, UUID examId) {
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new ExamNotFoundException(examId));

        UUID childId = exam.getChild().getChildId();
        UUID hospitalId = staffPrincipal.getHospitalId();

        // HospitalChildrenService를 통해 Child와 Hospital의 연동 여부 확인
        boolean isLinked = hospitalChildrenService.isChildLinkedToHospital(childId, hospitalId);

        if (!isLinked) {
            log.warn("HospitalStaff 권한 없음 - staffId: {}, hospitalId: {}, examId: {}, childId: {}",
                    staffPrincipal.getHospitalStaffId(), hospitalId, examId, childId);
            throw new ExamAccessDeniedException(examId);
        }

        log.debug("HospitalStaff 권한 검증 성공 - staffId: {}, hospitalId: {}, examId: {}",
                staffPrincipal.getHospitalStaffId(), hospitalId, examId);
    }

    /**
     * S3 Presigned GET URL 생성 (조회용)
     */
    public String generatePresignedGetUrl(String bucket, String s3Key, int expiresInSec) {
        try {
            GetObjectRequest getObjectRequest = GetObjectRequest.builder()
                    .bucket(bucket)
                    .key(s3Key)
                    .build();

            Duration expiration = Duration.ofSeconds(expiresInSec);

            GetObjectPresignRequest presignRequest = GetObjectPresignRequest.builder()
                    .signatureDuration(expiration)
                    .getObjectRequest(getObjectRequest)
                    .build();

            PresignedGetObjectRequest presignedRequest = s3Presigner.presignGetObject(presignRequest);

            return presignedRequest.url().toString();
        } catch (Exception e) {
            log.error("Presigned GET URL 생성 실패 - bucket: {}, key: {}", bucket, s3Key, e);
            throw new S3UploadException(e);
        }
    }

    /**
     * 특정 검사의 특정 태스크 영상 삭제 (자녀/보호자 권한 검증 + 삭제 가능한 상태 확인)
     * 처리 로직:
     * 1. 권한 확인 (자녀/보호자 본인의 검사인지)
     * 2. DB에서 video 조회
     * 3. 영상 상태가 삭제 가능한지 확인 (PENDING_UPLOAD, UPLOADED만 삭제 가능)
     * 4. MinIO에서 실제 파일 삭제 (DeleteObject는 파일이 없어도 성공 반환 - 멱등성)
     * 5. DB 업데이트 - status를 DELETED로 변경 (soft delete)
     */
    @Override
    @Transactional
    public VideoDeleteResponse deleteVideo(UUID userId, UUID examId, UUID videoId) {

        // 1. Video 조회
        Video video = videoRepository.findById(videoId)
                .orElseThrow(() -> new VideoNotFoundException(videoId));

        // 2. Video가 요청된 Exam에 속하는지 확인
        if (!video.getExam().getExamId().equals(examId)) {
            log.error("Video가 해당 Exam에 속하지 않음 - videoId: {}, examId: {}",
                    videoId, examId);
            throw new VideoNotFoundException(videoId);
        }

        // 3. 권한 검증
        if (!video.getExam().getChild().getUser().getUserId().equals(userId)) {
            throw new ExamAccessDeniedException(examId);
        }

        // 4. 영상 상태 확인
        if (!video.canDelete()) {
            log.warn("삭제 불가능한 영상 상태 - videoId: {}, status: {}",
                    video.getVideoId(), video.getVideoStatus());
            throw new InvalidVideoStatusException(video.getVideoStatus());
        }

        // 응답 생성에 필요한 정보 미리 저장
        String videoTypeStr = video.getVideoType().name();
        String videoIdStr = video.getVideoId().toString();

        // MinIO에서 파일 삭제
        boolean deletedFromStorage = deleteFromS3(video);

        // DB에서 완전 삭제
        videoRepository.delete(video);

        log.info("Video soft delete 완료 (by videoId) - videoId: {}, examId: {}, status: {}",
                videoId, examId, video.getVideoStatus());

        // 7. 응답 생성
        return VideoDeleteResponse.builder()
                .examId(examId.toString())
                .videoType(video.getVideoType().name())
                .videoId(video.getVideoId().toString())
                .deletedFromStorage(deletedFromStorage)
                .status(video.getVideoStatus().name())
                .build();
    }

    /**
     * S3에서 파일 삭제 (공통 로직)
     */
    private boolean deleteFromS3(Video video) {
        try {
            s3Client.deleteObject(builder -> builder
                    .bucket(video.getS3Bucket())
                    .key(video.getS3Key())
                    .build());
            log.info("MinIO 파일 삭제 완료 - bucket: {}, key: {}",
                    video.getS3Bucket(), video.getS3Key());
            return true;
        } catch (Exception e) {
            log.error("MinIO 파일 삭제 실패 - bucket: {}, key: {}",
                    video.getS3Bucket(), video.getS3Key(), e);
            return false;
        }
    }
}