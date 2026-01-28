package com.ssafy.aitime.domain.exam.service;

import java.util.UUID;

public interface VideoAnalysisService {
    /**
     * 검사(Exam)의 모든 영상(4개)에 대해 AI 분석 요청
     */
    void requestAnalysis(UUID examId);

    /**
     * 특정 영상 1개에 대해 AI 분석 요청
     */
    void requestSingleVideoAnalysis(UUID videoId);
}
