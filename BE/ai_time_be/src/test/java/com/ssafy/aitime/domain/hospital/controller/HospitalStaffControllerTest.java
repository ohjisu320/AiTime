package com.ssafy.aitime.domain.hospital.controller;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.hospital.dto.request.HospitalStaffLoginRequest;
import com.ssafy.aitime.domain.hospital.dto.response.DoctorListResponse;
import com.ssafy.aitime.domain.hospital.dto.response.StaffTokenResponse;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.service.HospitalStaffService;
import com.ssafy.aitime.domain.hospital.service.dto.HospitalStaffInfoDTO;
import com.ssafy.aitime.security.principal.HospitalStaffPrincipal;
import org.jspecify.annotations.Nullable;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import tools.jackson.databind.ObjectMapper;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(HospitalStaffController.class)
@AutoConfigureMockMvc(addFilters = false) // 시큐리티 필터는 제외하고 API 로직만 테스트
class HospitalStaffControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private HospitalStaffService hospitalStaffService;

    // 테스트용 고정 ID
    private static final UUID TEST_STAFF_ID = UUID.fromString("11111111-1111-1111-1111-111111111111");

    /**
     * @AuthenticationPrincipal HospitalStaffPrincipal 주입을 위한 설정
     */
    @TestConfiguration
    static class TestConfig implements WebMvcConfigurer {
        @Override
        public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
            resolvers.add(new HandlerMethodArgumentResolver() {
                @Override
                public boolean supportsParameter(org.springframework.core.MethodParameter parameter) {
                    return parameter.getParameterType().isAssignableFrom(HospitalStaffPrincipal.class);
                }

                @Override
                public @Nullable Object resolveArgument(org.springframework.core.MethodParameter parameter,
                                                        @Nullable ModelAndViewContainer mavContainer,
                                                        NativeWebRequest webRequest,
                                                        @Nullable WebDataBinderFactory binderFactory) {
                    Hospital hospital = Hospital.builder().name("테스트병원").build();
                    HospitalStaff staff = HospitalStaff.builder()
                            .loginId("testStaff")
                            .staffRole(StaffRole.DESK)
                            .hospital(hospital)
                            .recordStatus(RecordStatus.ACTIVE)
                            .build();
                    ReflectionTestUtils.setField(staff, "hospitalStaffId", TEST_STAFF_ID);
                    return HospitalStaffPrincipal.from(staff);
                }
            });
        }
    }

    @Test
    @DisplayName("병원 직원 로그인 성공 시 200 OK와 토큰을 반환한다")
    void loginSuccess() throws Exception {
        // given
        HospitalStaffLoginRequest request = new HospitalStaffLoginRequest("doctor01", "password123");

        UUID staffId = UUID.randomUUID();
        StaffTokenResponse tokenResponse = new StaffTokenResponse(
                "staff-access-token",
                "staff-refresh-token",
                new HospitalStaffInfoDTO(staffId, "김의사", StaffRole.DOCTOR)
        );

        when(hospitalStaffService.login(any(HospitalStaffLoginRequest.class)))
                .thenReturn(tokenResponse);

        // when & then
        mockMvc.perform(post("/hospital-staff/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(header().exists("Set-Cookie")) // 쿠키 생성 확인
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("로그인에 성공하였습니다."))
                .andExpect(jsonPath("$.data.accessToken").value("staff-access-token"))
                .andExpect(jsonPath("$.data.hospitalStaffInfoDTO.hospitalStaffId").value(staffId.toString()))
                .andExpect(jsonPath("$.data.hospitalStaffInfoDTO.name").value("김의사"))
                .andExpect(jsonPath("$.data.hospitalStaffInfoDTO.staffRole").value("DOCTOR"));
    }

    @Test
    @DisplayName("로그인 요청 시 loginId가 비어있으면 400 Bad Request를 반환한다")
    void loginFailByEmptyLoginId() throws Exception {
        // given
        HospitalStaffLoginRequest request = new HospitalStaffLoginRequest("", "password123");

        // when & then
        mockMvc.perform(post("/hospital-staff/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("로그인 요청 시 password가 비어있으면 400 Bad Request를 반환한다")
    void loginFailByEmptyPassword() throws Exception {
        // given
        HospitalStaffLoginRequest request = new HospitalStaffLoginRequest("doctor01", "");

        // when & then
        mockMvc.perform(post("/hospital-staff/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("리프레시 토큰 갱신 성공 시 200 OK와 새로운 토큰을 반환한다")
    void refreshSuccess() throws Exception {
        // given
        UUID staffId = UUID.randomUUID();
        StaffTokenResponse tokenResponse = new StaffTokenResponse(
                "new-access-token",
                "new-refresh-token",
                new HospitalStaffInfoDTO(staffId, "김의사", StaffRole.DOCTOR)
        );

        when(hospitalStaffService.refresh(anyString())).thenReturn(tokenResponse);

        // when & then
        mockMvc.perform(post("/hospital-staff/refresh")
                        .cookie(new jakarta.servlet.http.Cookie("refreshToken", "old-refresh-token")))
                .andExpect(status().isOk())
                .andExpect(header().exists("Set-Cookie")) // 쿠키 갱신 확인
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("토큰이 재발급되었습니다."))
                .andExpect(jsonPath("$.data.accessToken").value("new-access-token"))
                .andExpect(jsonPath("$.data.hospitalStaffInfoDTO.hospitalStaffId").value(staffId.toString()));
    }

    @Test
    @DisplayName("리프레시 요청 시 쿠키가 없으면 400 Bad Request를 반환한다")
    void refreshFailByNoCookie() throws Exception {
        // when & then
        mockMvc.perform(post("/hospital-staff/refresh"))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("로그아웃 성공 시 200 OK와 쿠키 삭제를 반환한다")
    void logoutSuccess() throws Exception {
        // given
        String accessToken = "Bearer valid-access-token";
        String refreshToken = "valid-refresh-token";

        // when & then
        mockMvc.perform(post("/hospital-staff/logout")
                        .header("Authorization", accessToken)
                        .cookie(new jakarta.servlet.http.Cookie("refreshToken", refreshToken)))
                .andExpect(status().isOk())
                .andExpect(header().exists("Set-Cookie"))
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("로그아웃 되었습니다."));

        verify(hospitalStaffService, times(1)).logout(eq("valid-access-token"), eq(refreshToken));
    }

    @Test
    @DisplayName("로그아웃 시 Authorization 헤더가 없어도 200 OK를 반환한다")
    void logoutWithoutAuthorizationHeader() throws Exception {
        // given
        String refreshToken = "valid-refresh-token";

        // when & then
        mockMvc.perform(post("/hospital-staff/logout")
                        .cookie(new jakarta.servlet.http.Cookie("refreshToken", refreshToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("로그아웃 되었습니다."));

        verify(hospitalStaffService, times(1)).logout(isNull(), eq(refreshToken));
    }

    @Test
    @DisplayName("로그아웃 시 RefreshToken 쿠키가 없어도 200 OK를 반환한다")
    void logoutWithoutRefreshTokenCookie() throws Exception {
        // given
        String accessToken = "Bearer valid-access-token";

        // when & then
        mockMvc.perform(post("/hospital-staff/logout")
                        .header("Authorization", accessToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("로그아웃 되었습니다."));

        verify(hospitalStaffService, times(1)).logout(eq("valid-access-token"), isNull());
    }

    @Test
    @DisplayName("로그아웃 시 모든 토큰이 없어도 200 OK를 반환한다")
    void logoutWithoutAnyToken() throws Exception {
        // when & then
        mockMvc.perform(post("/hospital-staff/logout"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("로그아웃 되었습니다."));

        verify(hospitalStaffService, times(1)).logout(isNull(), isNull());
    }
}