package com.ssafy.aitime.domain.hospital.dto.response;

import com.ssafy.aitime.domain.exam.dto.response.AdosDetailResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamWithVideosResponse;

import java.util.List;

public record InitialReportResponse(
        List<ExamWithVideosResponse> examVideoList,
        LatestPoseVideoResponse latestPoseImitationVideo,
        AdosReportGraphsResponse adosGraphs,
        AdosDetailResponse latestAdosDetail
) {
}
