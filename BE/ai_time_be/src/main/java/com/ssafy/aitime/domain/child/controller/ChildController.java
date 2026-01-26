package com.ssafy.aitime.domain.child.controller;

import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.response.ChildCreateResponse;
import com.ssafy.aitime.domain.child.service.ChildService;
import com.ssafy.aitime.security.principal.UserPrincipal;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/child")
@RequiredArgsConstructor
public class ChildController {

    private final ChildService childService;

    @PostMapping
    public ResponseEntity<ApiResponse<ChildCreateResponse>> addChild(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody ChildCreateRequest request
    ) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created("아이 등록이 완료되었습니다.", childService.addChild(principal.getUserId(), request)));
    }
}
