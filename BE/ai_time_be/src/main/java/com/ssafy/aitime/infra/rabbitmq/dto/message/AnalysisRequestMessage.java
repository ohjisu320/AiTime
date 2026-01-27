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
                .s3Uri(String.format("s3://%s/%s", video.getS3Bucket(), video.getS3Key()))
                .build();
    }

    private static Integer mapVideoTypeToTaskNo(com.ssafy.aitime.domain.exam.entity.enums.VideoType videoType) {
        return switch (videoType) {
            case TASK1 -> 1;           // 대면 호명반응 NAME_FACING
            case TASK2 -> 2;      // 발화 모방행동 SPEECH_IMITATION
            case TASK3 -> 3;        // 동작 모방행동 POSE_IMITATION
            case TASK4 -> 4;       // 비대면 호명반응 NAME_NON_FACING
        };
    }

    public String getQueueName() {
        return "analysis.req.task" + taskNo;
    }
}
