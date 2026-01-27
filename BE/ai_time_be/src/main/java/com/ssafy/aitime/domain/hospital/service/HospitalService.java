package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.domain.child.dto.response.HospitalInfo;

import java.util.List;
import java.util.UUID;

public interface HospitalService {
    List<HospitalInfo> getLinkedHospitalsByChild(UUID childId);
}
