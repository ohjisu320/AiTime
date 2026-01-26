package com.ssafy.aitime.domain.hospital.controller;

import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.ChildResponse;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;
import com.ssafy.aitime.domain.hospital.service.DoctorService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.ObjectMapper;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(DoctorController.class)
@DisplayName("DoctorController 테스트")
class DoctorControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private DoctorService doctorService;

    private static final UUID TEST_DOCTOR_ID = UUID.fromString("550e8400-e29b-41d4-a716-446655440000");
    private static final UUID TEST_CHILD_ID = UUID.fromString("660e8400-e29b-41d4-a716-446655440001");
    private static final UUID TEST_USER_ID = UUID.fromString("770e8400-e29b-41d4-a716-446655440002");

    @Test
    @DisplayName("환자 목록 조회 성공 - 기본 요청")
    void getSearchPatientList_Success() throws Exception {
        // given
        PatientSearchResponse mockResponse = new PatientSearchResponse(
                Collections.emptyList(),
                0L
        );

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("OK"))
                .andExpect(jsonPath("$.data").exists())
                .andExpect(jsonPath("$.data.total").value(0))
                .andExpect(jsonPath("$.data.childResponses").isArray());

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 환자 데이터 포함")
    void getSearchPatientList_WithData_Success() throws Exception {
        // given
        List<ChildResponse> children = new ArrayList<>();
        children.add(new ChildResponse(
                TEST_CHILD_ID,
                TEST_USER_ID,
                "홍길동",
                12,
                LocalDate.of(2023, 1, 15),
                "MALE",
                "COMPLETED"
        ));

        PatientSearchResponse mockResponse = new PatientSearchResponse(children, 1L);

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.total").value(1))
                .andExpect(jsonPath("$.data.childResponses[0].childId").value(TEST_CHILD_ID.toString()))
                .andExpect(jsonPath("$.data.childResponses[0].name").value("홍길동"))
                .andExpect(jsonPath("$.data.childResponses[0].monthlyAge").value(12))
                .andExpect(jsonPath("$.data.childResponses[0].gender").value("MALE"))
                .andExpect(jsonPath("$.data.childResponses[0].latestExamStatus").value("COMPLETED"));

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 이름 검색")
    void getSearchPatientList_WithName_Success() throws Exception {
        // given
        String searchName = "홍길동";
        PatientSearchResponse mockResponse = new PatientSearchResponse(
                Collections.emptyList(),
                0L
        );

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("name", searchName)
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").exists());

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 날짜 검색 (date)")
    void getSearchPatientList_WithDate_Success() throws Exception {
        // given
        PatientSearchResponse mockResponse = new PatientSearchResponse(
                Collections.emptyList(),
                0L
        );

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("date", "2024-01-15")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 날짜 검색 (year, month, day)")
    void getSearchPatientList_WithYearMonthDay_Success() throws Exception {
        // given
        PatientSearchResponse mockResponse = new PatientSearchResponse(
                Collections.emptyList(),
                0L
        );

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("year", "2024")
                        .param("month", "1")
                        .param("day", "15")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 결과 상태 필터")
    void getSearchPatientList_WithResultStatus_Success() throws Exception {
        // given
        PatientSearchResponse mockResponse = new PatientSearchResponse(
                Collections.emptyList(),
                0L
        );

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("resultStatus", "COMPLETED")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 페이징 파라미터")
    void getSearchPatientList_WithPaging_Success() throws Exception {
        // given
        PatientSearchResponse mockResponse = new PatientSearchResponse(
                Collections.emptyList(),
                0L
        );

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("page", "1")
                        .param("size", "20")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 헤더 없이 기본값 사용")
    void getSearchPatientList_WithoutHeader_UseDefault() throws Exception {
        // given
        PatientSearchResponse mockResponse = new PatientSearchResponse(
                Collections.emptyList(),
                0L
        );

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 모든 필터 조합")
    void getSearchPatientList_WithAllFilters_Success() throws Exception {
        // given
        PatientSearchResponse mockResponse = new PatientSearchResponse(
                Collections.emptyList(),
                0L
        );

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("name", "홍길동")
                        .param("date", "2024-01-15")
                        .param("resultStatus", "COMPLETED")
                        .param("page", "0")
                        .param("size", "10")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").exists());

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }

    @Test
    @DisplayName("환자 목록 조회 실패 - 유효하지 않은 UUID 형식")
    void getSearchPatientList_InvalidUUID_Fail() throws Exception {
        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", "invalid-uuid")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("환자 목록 조회 실패 - 음수 페이지")
    void getSearchPatientList_NegativePage_Fail() throws Exception {
        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("page", "-1")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("환자 목록 조회 실패 - 0 이하 사이즈")
    void getSearchPatientList_InvalidSize_Fail() throws Exception {
        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("size", "0")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("환자 목록 조회 실패 - 최대 사이즈 초과 (101)")
    void getSearchPatientList_ExceedMaxSize_Fail() throws Exception {
        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("size", "101")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("환자 목록 조회 실패 - 잘못된 날짜 형식")
    void getSearchPatientList_InvalidDateFormat_Fail() throws Exception {
        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .param("date", "2024/01/15")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("환자 목록 조회 성공 - 여러 환자 데이터")
    void getSearchPatientList_MultipleChildren_Success() throws Exception {
        // given
        List<ChildResponse> children = new ArrayList<>();
        children.add(new ChildResponse(
                UUID.randomUUID(),
                UUID.randomUUID(),
                "홍길동",
                12,
                LocalDate.of(2023, 1, 15),
                "MALE",
                "COMPLETED"
        ));
        children.add(new ChildResponse(
                UUID.randomUUID(),
                UUID.randomUUID(),
                "김철수",
                24,
                LocalDate.of(2022, 3, 20),
                "MALE",
                "PENDING"
        ));

        PatientSearchResponse mockResponse = new PatientSearchResponse(children, 2L);

        given(doctorService.getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class)))
                .willReturn(mockResponse);

        // when & then
        mockMvc.perform(get("/doctor/patients")
                        .header("X-DOCTOR-ID", TEST_DOCTOR_ID.toString())
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.total").value(2))
                .andExpect(jsonPath("$.data.childResponses").isArray())
                .andExpect(jsonPath("$.data.childResponses.length()").value(2))
                .andExpect(jsonPath("$.data.childResponses[0].name").value("홍길동"))
                .andExpect(jsonPath("$.data.childResponses[1].name").value("김철수"));

        verify(doctorService).getSearchPatientList(eq(TEST_DOCTOR_ID), any(PatientSearchRequest.class));
    }
}