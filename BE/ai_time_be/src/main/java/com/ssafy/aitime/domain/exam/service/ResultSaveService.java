package com.ssafy.aitime.domain.exam.service;

import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.infra.rabbitmq.dto.message.AnalysisResultMessage;

import java.util.List;

public interface ResultSaveService {

    void saveResult(Video video, AnalysisResultMessage result);
}
