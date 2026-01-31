package com.ssafy.aitime.infra.rabbitmq.dto.message;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.aitime.domain.exam.entity.Video;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class AnalysisRequestMessage {

    @JsonProperty("schema_version")
    private String schemaVersion;

    @JsonProperty("job_id")
    private String jobId;  // exam.examId.toString()

    @JsonProperty("task_no")
    private Integer taskNo;  // videoType에 따라 1~4

    @JsonProperty("age_months")
    private Long ageMonths;

    @JsonProperty("s3_uri")
    private String s3Uri;  // s3://bucket/key

    // 정적 팩토리 메서드
    public static AnalysisRequestMessage from(Video video, Long ageMonths) {
        return AnalysisRequestMessage.builder()
                .schemaVersion("1.0")
                .jobId(video.getExam().getExamId().toString())
                .taskNo(mapVideoTypeToTaskNo(video.getVideoType()))
                .ageMonths(ageMonths)
                .s3Uri(String.format("s3://%s/%s", video.getS3Bucket(), video.getS3Url()))
                .build();
    }

    private static Integer mapVideoTypeToTaskNo(com.ssafy.aitime.domain.exam.entity.enums.VideoType videoType) {
        return switch (videoType) {
            case POSE_IMITATION -> 1;      // task1: 동작 모방행동
            case SPEECH_IMITATION -> 2;    // task2: 발화 모방행동
            case NAME_FACING -> 3;         // task3: 대면 호명반응
            case NAME_NON_FACING -> 4;     // task4: 비대면 호명반응
        };
    }

    public String getQueueName() {
        return "analysis.req.task" + taskNo;
    }
}
