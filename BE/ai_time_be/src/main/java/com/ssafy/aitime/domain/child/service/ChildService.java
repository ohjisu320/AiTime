package com.ssafy.aitime.domain.child.service;

import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.response.ChildInfoResponse;

import java.util.List;
import java.util.UUID;

public interface ChildService {
    ChildInfoResponse addChild(UUID userId, ChildCreateRequest request);
    List<ChildInfoResponse> getChildList(UUID userId);
}
