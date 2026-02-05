package com.ssafy.aitime.domain.exam.dto.response;

import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import lombok.Builder;

import java.util.List;

@Builder
public record ExamInfoResponse(
        String examId,
        boolean underEighteen,  // 18개월 미만 여부 (true: 12-17개월, false: 18-23개월)
        ExamStatus status,
        List<VideoTaskInfo> videoTasks
) {
    @Builder
    public record VideoTaskInfo(
        String videoType,   // POSE_IMITATION, SPEECH_IMITATION, NAME_FACING, NAME_NON_FACING
        String status,     // UPLOADED, EMPTY
        String videoId     // 업로드된 경우 videoId, 아니면 null
    )   {}
}