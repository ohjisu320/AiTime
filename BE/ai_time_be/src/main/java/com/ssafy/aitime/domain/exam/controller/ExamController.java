package com.ssafy.aitime.domain.exam.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildAgeInfoResponse;
import com.ssafy.aitime.domain.child.service.ChildService;
import com.ssafy.aitime.domain.exam.dto.response.ExamInfoResponse;
import com.ssafy.aitime.domain.exam.service.ExamService;
import com.ssafy.aitime.security.principal.UserPrincipal;
import lombok.RequiredArgsConstructor;
import org.jetbrains.annotations.NotNull;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/exam")
@RequiredArgsConstructor
public class ExamController {

    private final ExamService examService;
    private final ChildService childService;

    /**
     * 5. 검사 진행도 조회
     * GET /api/v1/exam/{childId}/examInfo
     * 4개의 태스크(TASK1~4)별 영상 업로드 완료 여부를 확인합니다.
     */
    @GetMapping("/{childId}/examInfo")
    public ResponseEntity<ApiResponse<ExamInfoResponse>> getExamInfo(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable @NotNull UUID childId
    ) {
        // 순환참조때문에 여기서 child 권한 확인 및 개월 수 정보 조회함
        // 1. Child 권한 확인 및 개월 수 정보 조회
        ChildAgeInfoResponse childAgeInfo = childService.validateAndGetChildAgeInfo(
                principal.getUserId(), childId);
        // 2. Exam 정보 조회
        ExamInfoResponse examInfo = examService.getExamInfo(
                childId, childAgeInfo.underEighteen());

        return ResponseEntity.ok(
                ApiResponse.ok("검사 진행도 조회가 완료되었습니다.", examInfo));
    }
}
