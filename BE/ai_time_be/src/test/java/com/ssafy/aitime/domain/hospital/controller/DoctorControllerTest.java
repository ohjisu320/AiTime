package com.ssafy.aitime.domain.hospital.controller;

import com.ssafy.aitime.domain.hospital.dto.response.TotalPatientListResponse;
import com.ssafy.aitime.domain.hospital.service.DoctorService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.eq;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(controllers = DoctorController.class)
class DoctorControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private DoctorService doctorService;

    @Test
    @DisplayName("GET /doctors/me/patients - X-DOCTOR-ID 헤더가 있으면 정상 응답")
    void totalPatientList_withHeader_success() throws Exception {
        // given
        UUID doctorId = UUID.fromString("550e8400-e29b-41d4-a716-446655440000");

        // record DTO는 생성자로 바로 생성
        TotalPatientListResponse response =
                new TotalPatientListResponse(List.of(), 0L);

        Mockito.when(doctorService.getTotalPatientList(eq(doctorId)))
                .thenReturn(response);

        // when & then
        mockMvc.perform(
                        get("/doctors/me/patients")
                                .header("X-DOCTOR-ID", doctorId.toString())
                                .accept(MediaType.APPLICATION_JSON)
                )
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON));

        Mockito.verify(doctorService).getTotalPatientList(eq(doctorId));
    }

    @Test
    @DisplayName("GET /doctors/me/patients - 헤더가 없으면 defaultValue 사용")
    void totalPatientList_withoutHeader_usesDefaultValue() throws Exception {
        // given
        UUID defaultDoctorId =
                UUID.fromString("550e8400-e29b-41d4-a716-446655440000");

        TotalPatientListResponse response =
                new TotalPatientListResponse(List.of(), 0L);

        Mockito.when(doctorService.getTotalPatientList(eq(defaultDoctorId)))
                .thenReturn(response);

        // when & then
        mockMvc.perform(
                        get("/doctors/me/patients")
                                .accept(MediaType.APPLICATION_JSON)
                )
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON));

        Mockito.verify(doctorService).getTotalPatientList(eq(defaultDoctorId));
    }
}
