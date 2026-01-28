package com.ssafy.aitime.domain.exam.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.exam.service.VideoAnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/exams-analysis")
@RequiredArgsConstructor
public class ExamAnalysisController {

    private final VideoAnalysisService videoAnalysisService;

    /**
     * 검사 분석 시작 (4개 영상 모두)
     */
    @PostMapping("/{examId}/analyze")
    public ResponseEntity<ApiResponse<String>> startAnalysis(@PathVariable UUID examId) {
        videoAnalysisService.requestAnalysis(examId);
        return ResponseEntity.ok(ApiResponse.ok("분석 요청이 완료되었습니다."));
    }

    /**
     * 특정 영상만 재분석
     */
    @PostMapping("/videos/{videoId}/analyze")
    public ResponseEntity<ApiResponse<String>> startSingleVideoAnalysis(@PathVariable UUID videoId) {
        videoAnalysisService.requestSingleVideoAnalysis(videoId);
        return ResponseEntity.ok(ApiResponse.ok("영상 분석 요청이 완료되었습니다."));
    }
}
