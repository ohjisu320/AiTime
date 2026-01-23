package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.response.TotalPatientListResponse;

import java.util.UUID;

public interface DoctorService {
    public TotalPatientListResponse getTotalPatientList(UUID doctorId);
}
