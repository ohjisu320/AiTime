package com.ssafy.aitime.domain.child.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.request.ChildDeleteResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildHomeResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildHospitalListResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildInfoResponse;
import com.ssafy.aitime.domain.child.service.ChildService;
import com.ssafy.aitime.security.principal.UserPrincipal;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.jetbrains.annotations.NotNull;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/child")
@RequiredArgsConstructor
public class ChildController {

    private final ChildService childService;

    @PostMapping
    public ResponseEntity<ApiResponse<ChildInfoResponse>> addChild(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody ChildCreateRequest request
    ) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created("아이 등록이 완료되었습니다.", childService.addChild(principal.getUserId(), request)));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<ChildInfoResponse>>> getChildren(
            @AuthenticationPrincipal UserPrincipal principal
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok("아이 목록 조회가 완료되었습니다.", childService.getChildList(principal.getUserId()))
        );
    }

    @DeleteMapping("/{childId}")
    public ResponseEntity<ApiResponse<ChildDeleteResponse>> deleteChild(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable("childId") UUID childId
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok("아이 정보가 성공적으로 삭제되었습니다.", childService.deleteChild(principal.getUserId(), childId))
        );
    }

    @GetMapping("/{childId}")
    public ResponseEntity<ApiResponse<ChildHomeResponse>> getChildHome(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable @NotNull UUID childId // null 체크
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok("아이 홈 정보가 성공적으로 조회되었습니다.",childService.getChildHomeInfo(principal.getUserId(),childId)));
    }
}
