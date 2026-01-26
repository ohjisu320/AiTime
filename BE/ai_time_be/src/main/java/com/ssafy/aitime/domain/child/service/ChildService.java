package com.ssafy.aitime.domain.child.service;

import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.response.ChildCreateResponse;

import java.util.UUID;

public interface ChildService {
    ChildCreateResponse addChild(UUID userId, ChildCreateRequest request);
}
