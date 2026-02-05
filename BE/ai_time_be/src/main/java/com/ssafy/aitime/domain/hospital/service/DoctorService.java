package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.exam.dto.response.ExamWithVideosResponse;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;

import java.util.List;
import java.util.UUID;

public interface DoctorService {
    PatientSearchResponse getSearchPatientList(UUID doctorId, PatientSearchRequest patientSearchRequest);
    /**
     * 특정 환아의 검사 목록 조회 (비디오 목록 포함)
     */
    List<ExamWithVideosResponse> getExamsByHospitalChildren(UUID hospitalStaffId, UUID hospitalChildrenId);
}
