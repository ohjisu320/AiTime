package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;

import java.util.UUID;

public interface DoctorService {
    PatientSearchResponse getSearchPatientList(UUID doctorId, PatientSearchRequest patientSearchRequest);
}
