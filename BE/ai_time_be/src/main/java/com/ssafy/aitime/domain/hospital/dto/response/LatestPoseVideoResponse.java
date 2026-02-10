package com.ssafy.aitime.domain.hospital.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record LatestPoseVideoResponse(
        String videoId,
        String videoType,
        String examId,
        String bucket,
        String s3Key,
        String viewUrl,
        LocalDateTime expiresAt,
        List<TimestampDTO> timestamps
) {
    public record TimestampDTO(
            Double parentStartTime,
            Double parentEndTime,
            Double childStartTime,
            Double childEndTime,
            Integer trialIndex
    ) {}
}
