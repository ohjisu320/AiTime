package com.ssafy.aitime.domain.exam.service;


import java.util.UUID;

public interface AdosCalculationService {
    void calculateAndSaveAdos(UUID examId);
}
