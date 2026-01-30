package com.ssafy.aitime.domain.child.service;

import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.request.ChildDeleteResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildAgeInfoResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildHomeResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildInfoResponse;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.exam.dto.response.ExamStartResponse;
import com.ssafy.aitime.domain.hospital.dto.response.HospitalResponseDto;

import java.util.List;
import java.util.UUID;

public interface ChildService {
    ChildInfoResponse addChild(UUID userId, ChildCreateRequest request);
    List<ChildInfoResponse> getChildList(UUID userId);
    ChildDeleteResponse deleteChild(UUID userId, UUID childId);

    ChildHomeResponse getChildHomeInfo(UUID userId, UUID childId);
}
