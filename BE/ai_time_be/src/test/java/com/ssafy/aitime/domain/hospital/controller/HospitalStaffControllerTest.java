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
import com.ssafy.aitime.domain.hospital.service.ReservationService;
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

import java.time.LocalDate;
import java.time.YearMonth;
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

    @MockitoBean
    private ReservationService reservationService;

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
                    ReflectionTestUtils.setField(hospital, "hospitalId", UUID.fromString("22222222-2222-2222-2222-222222222222"));

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

// 기존 캘린더 관련 테스트들을 모두 삭제하고 아래로 교체

    @Test
    @DisplayName("캘린더 인디케이터 정보를 조회하면 200 상태코드와 날짜 목록을 반환한다")
    void getReservationDates_Success() throws Exception {
        // given
        int year = 2026;
        int month = 1;

        List<LocalDate> dates = List.of(
                LocalDate.of(2026, 1, 5),
                LocalDate.of(2026, 1, 12),
                LocalDate.of(2026, 1, 20),
                LocalDate.of(2026, 1, 21)
        );

        given(reservationService.getHospitalReservationDates(any(UUID.class), eq(year), eq(month)))
                .willReturn(dates);

        // when & then
        mockMvc.perform(get("/hospital-staff/calendar")
                        .param("year", "2026")
                        .param("month", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("달력 인디케이터 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data.length()").value(4))
                .andExpect(jsonPath("$.data[0]").value("2026-01-05"))
                .andExpect(jsonPath("$.data[1]").value("2026-01-12"))
                .andExpect(jsonPath("$.data[2]").value("2026-01-20"))
                .andExpect(jsonPath("$.data[3]").value("2026-01-21"));
    }

    @Test
    @DisplayName("예약이 없는 월은 200 상태코드와 빈 배열을 반환한다")
    void getReservationDates_EmptyResult() throws Exception {
        // given
        int year = 2026;
        int month = 12;

        given(reservationService.getHospitalReservationDates(any(UUID.class), eq(year), eq(month)))
                .willReturn(List.of());

        // when & then
        mockMvc.perform(get("/hospital-staff/calendar")
                        .param("year", "2026")
                        .param("month", "12"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("200 OK"))
                .andExpect(jsonPath("$.message").value("달력 인디케이터 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data.length()").value(0));
    }

    @Test
    @DisplayName("인증된 사용자의 병원 ID로 캘린더를 조회한다")
    void getReservationDates_UsesAuthenticatedHospitalId() throws Exception {
        // given
        int year = 2026;
        int month = 1;
        UUID expectedHospitalId = UUID.fromString("22222222-2222-2222-2222-222222222222");

        given(reservationService.getHospitalReservationDates(eq(expectedHospitalId), eq(year), eq(month)))
                .willReturn(List.of());

        // when
        mockMvc.perform(get("/hospital-staff/calendar")
                        .param("year", "2026")
                        .param("month", "1"))
                .andExpect(status().isOk());

        // then
        verify(reservationService, times(1))
                .getHospitalReservationDates(eq(expectedHospitalId), eq(year), eq(month));
    }

    @Test
    @DisplayName("year 파라미터가 누락되면 400 Bad Request를 반환한다")
    void getReservationDates_MissingYear() throws Exception {
        // when & then
        mockMvc.perform(get("/hospital-staff/calendar")
                        .param("month", "1"))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("month 파라미터가 누락되면 400 Bad Request를 반환한다")
    void getReservationDates_MissingMonth() throws Exception {
        // when & then
        mockMvc.perform(get("/hospital-staff/calendar")
                        .param("year", "2026"))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("다양한 월에 대해 정상적으로 조회한다")
    void getReservationDates_VariousMonths() throws Exception {
        // given - 2월
        given(reservationService.getHospitalReservationDates(any(UUID.class), eq(2026), eq(2)))
                .willReturn(List.of(LocalDate.of(2026, 2, 14)));

        // when & then - 2월
        mockMvc.perform(get("/hospital-staff/calendar")
                        .param("year", "2026")
                        .param("month", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data[0]").value("2026-02-14"));

        // given - 12월
        given(reservationService.getHospitalReservationDates(any(UUID.class), eq(2026), eq(12)))
                .willReturn(List.of(LocalDate.of(2026, 12, 25)));

        // when & then - 12월
        mockMvc.perform(get("/hospital-staff/calendar")
                        .param("year", "2026")
                        .param("month", "12"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data[0]").value("2026-12-25"));
    }


}