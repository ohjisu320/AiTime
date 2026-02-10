package com.ssafy.aitime.domain.hospital.dto.response;

import java.util.List;
import java.util.Map;

public record AdosReportGraphsResponse(
        List<String> xAxis,
        GraphGroups graphs
) {
    public record GraphGroups(
            GraphSeries graph1,
            GraphSeries graph2,
            GraphSeries graph3,
            GraphSeries graph4
    ) {}

    public record GraphSeries(
            Map<String, List<Integer>> series
    ) {}
}
