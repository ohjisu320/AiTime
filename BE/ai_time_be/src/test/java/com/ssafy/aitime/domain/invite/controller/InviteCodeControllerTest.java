package com.ssafy.aitime.domain.invite.controller;

import com.ssafy.aitime.domain.invite.dto.response.UnregisteredPatientResponse;
import tools.jackson.databind.ObjectMapper;
import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.invite.dto.request.InviteCodeRequest;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeResponse;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeRevokeResponse;
import com.ssafy.aitime.domain.invite.dto.response.InviteCodeStatusResponse;
import com.ssafy.aitime.domain.invite.entity.enums.InviteCodeStatus;
import com.ssafy.aitime.domain.invite.service.InviteCodeService;
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

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(InviteCodeController.class)
@AutoConfigureMockMvc(addFilters = false) // 시큐리티 필터 체인 통과
class InviteCodeControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private InviteCodeService inviteCodeService;

    @Autowired
    private ObjectMapper objectMapper;

    // 테스트에서 사용할 고정 ID들
    private static final UUID TEST_STAFF_ID = UUID.fromString("11111111-1111-1111-1111-111111111111");
    private static final UUID TEST_HOSPITAL_ID = UUID.fromString("22222222-2222-2222-2222-222222222222");

    /**
     * @AuthenticationPrincipal HospitalStaffPrincipal 에 가짜 객체를 주입하기 위한 설정
     */
    @TestConfiguration
    static class TestConfig implements WebMvcConfigurer {
        @Override
        public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
            resolvers.add(new HandlerMethodArgumentResolver() {
                @Override
                public boolean supportsParameter(org.springframework.core.MethodParameter parameter) {
                    // 컨트롤러 파라미터가 HospitalStaffPrincipal 타입인지 확인
                    return parameter.getParameterType().isAssignableFrom(HospitalStaffPrincipal.class);
                }

                @Override
                public @Nullable Object resolveArgument(org.springframework.core.MethodParameter parameter,
                                                        @Nullable ModelAndViewContainer mavContainer,
                                                        NativeWebRequest webRequest,
                                                        @Nullable WebDataBinderFactory binderFactory) {
                    // 가짜 병원 생성
                    Hospital hospital = Hospital.builder()
                            .name("테스트병원")
                            .build();
                    ReflectionTestUtils.setField(hospital, "hospitalId", TEST_HOSPITAL_ID);

                    // 가짜 스태프 생성
                    HospitalStaff staff = HospitalStaff.builder()
                            .loginId("staffUser")
                            .staffRole(StaffRole.DESK)
                            .hospital(hospital)
                            .recordStatus(RecordStatus.ACTIVE)
                            .build();
                    ReflectionTestUtils.setField(staff, "hospitalStaffId", TEST_STAFF_ID);

                    // Principal 객체로 변환하여 반환
                    return HospitalStaffPrincipal.from(staff);
                }
            });
        }
    }

    @Test
    @DisplayName("신규 초대코드를 발급하면 201 상태코드와 발급 정보를 반환한다")
    void createInviteCode_Success() throws Exception {
        // given
        InviteCodeRequest request = new InviteCodeRequest(
                "박튼튼",
                LocalDate.of(2024, 5, 20),
                "01012345678",
                LocalDateTime.of(2026, 2, 10, 14, 0),
                UUID.randomUUID()
        );

        InviteCodeResponse response = new InviteCodeResponse(
                UUID.randomUUID(),
                "FTL-ABCD-12",
                "박튼튼",
                "01012345678",
                InviteCodeStatus.ISSUED,
                LocalDateTime.now()
        );

        given(inviteCodeService.generateInviteCode(any(InviteCodeRequest.class), any(UUID.class)))
                .willReturn(response);

        // when & then
        mockMvc.perform(post("/invite-code")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.message").value("초대코드가 성공적으로 발급되었습니다."))
                .andExpect(jsonPath("$.data.inviteCode").value("FTL-ABCD-12"))
                .andExpect(jsonPath("$.data.childName").value("박튼튼"));
    }

    @Test
    @DisplayName("초대코드를 취소하면 200 상태코드와 취소 정보를 반환한다")
    void revokeInviteCode_Success() throws Exception {
        // given
        UUID inviteCodeId = UUID.randomUUID();
        InviteCodeRevokeResponse response = new InviteCodeRevokeResponse(
                inviteCodeId,
                InviteCodeStatus.REVOKED,
                LocalDateTime.now()
        );

        given(inviteCodeService.revokeInviteCode(any(UUID.class), any(UUID.class)))
                .willReturn(response);

        // when & then
        mockMvc.perform(delete("/invite-code/{inviteCodeId}", inviteCodeId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("초대코드가 성공적으로 삭제(취소)되었습니다."))
                .andExpect(jsonPath("$.data.status").value("REVOKED"));
    }

    @Test
    @DisplayName("초대코드의 상태를 조회하면 200 상태코드와 상태 정보를 반환한다")
    void getStatus_Success() throws Exception {
        // given
        UUID inviteCodeId = UUID.randomUUID();
        InviteCodeStatusResponse response = new InviteCodeStatusResponse(
                inviteCodeId,
                InviteCodeStatus.ISSUED,
                "박튼튼"
        );

        given(inviteCodeService.getInviteCodeStatus(any(UUID.class)))
                .willReturn(response);

        // when & then
        mockMvc.perform(get("/invite-code/{inviteCodeId}/status", inviteCodeId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("초대코드 상태 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data.status").value("ISSUED"))
                .andExpect(jsonPath("$.data.childName").value("박튼튼"));
    }

    @Test
    @DisplayName("날짜별 등록 대기 환아 목록을 조회하면 200 상태코드와 환아 목록을 반환한다")
    void getUnregisteredPatients_Success() throws Exception {
        // given
        int year = 2026;
        int month = 1;
        int day = 20;

        List<UnregisteredPatientResponse> responses = List.of(
                new UnregisteredPatientResponse(
                        UUID.randomUUID(),          // inviteCodeId
                        "INVITE-0001",              // inviteCode
                        "박튼튼",                    // childName
                        14,                         // childMonths
                        "01012345678",              // parentPhone
                        LocalDateTime.of(2026, 1, 20, 10, 0), // scheduledAt
                        "ISSUED"                    // status
                ),
                new UnregisteredPatientResponse(
                        UUID.randomUUID(),
                        "INVITE-0002",
                        "김건강",
                        19,
                        "01087654321",
                        LocalDateTime.of(2026, 1, 20, 14, 30),
                        "ISSUED"
                )
        );

        given(inviteCodeService.getUnregisteredPatients(any(UUID.class), eq(year), eq(month), eq(day)))
                .willReturn(responses);

        // when & then
        mockMvc.perform(get("/invite-code/patients")
                        .param("year", String.valueOf(year))
                        .param("month", String.valueOf(month))
                        .param("day", String.valueOf(day)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("날짜별 등록 대기 환아 목록 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data.length()").value(2))

                // 1번째
                .andExpect(jsonPath("$.data[0].inviteCodeId").exists())
                .andExpect(jsonPath("$.data[0].inviteCode").value("INVITE-0001"))
                .andExpect(jsonPath("$.data[0].childName").value("박튼튼"))
                .andExpect(jsonPath("$.data[0].childMonths").value(14))
                .andExpect(jsonPath("$.data[0].parentPhone").value("01012345678"))
                .andExpect(jsonPath("$.data[0].status").value("ISSUED"))

                // 2번째
                .andExpect(jsonPath("$.data[1].inviteCodeId").exists())
                .andExpect(jsonPath("$.data[1].inviteCode").value("INVITE-0002"))
                .andExpect(jsonPath("$.data[1].childName").value("김건강"))
                .andExpect(jsonPath("$.data[1].childMonths").value(19))
                .andExpect(jsonPath("$.data[1].parentPhone").value("01087654321"))
                .andExpect(jsonPath("$.data[1].status").value("ISSUED"));
    }


    @Test
    @DisplayName("조회 결과가 없으면 200 상태코드와 빈 배열을 반환한다")
    void getUnregisteredPatients_EmptyResult() throws Exception {
        // given
        int year = 2026;
        int month = 12;
        int day = 31;

        given(inviteCodeService.getUnregisteredPatients(any(UUID.class), eq(year), eq(month), eq(day)))
                .willReturn(List.of());

        // when & then
        mockMvc.perform(get("/invite-code/patients")
                        .param("year", String.valueOf(year))
                        .param("month", String.valueOf(month))
                        .param("day", String.valueOf(day)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("날짜별 등록 대기 환아 목록 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data.length()").value(0));
    }

    @Test
    @DisplayName("필수 파라미터가 누락되면 400 Bad Request를 반환한다")
    void getUnregisteredPatients_MissingParameter() throws Exception {
        // when & then - year만 있고 month, day 누락
        mockMvc.perform(get("/invite-code/patients")
                        .param("year", "2026"))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("인증된 사용자의 병원 ID로 조회한다")
    void getUnregisteredPatients_UsesAuthenticatedHospitalId() throws Exception {
        // given
        int year = 2026;
        int month = 1;
        int day = 20;

        given(inviteCodeService.getUnregisteredPatients(eq(TEST_HOSPITAL_ID), eq(year), eq(month), eq(day)))
                .willReturn(List.of());

        // when
        mockMvc.perform(get("/invite-code/patients")
                        .param("year", String.valueOf(year))
                        .param("month", String.valueOf(month))
                        .param("day", String.valueOf(day)))
                .andExpect(status().isOk());

        // then - 인증된 사용자의 병원 ID가 사용되었는지 검증
        verify(inviteCodeService, times(1))
                .getUnregisteredPatients(eq(TEST_HOSPITAL_ID), eq(year), eq(month), eq(day));
    }

    // InviteCodeControllerTest.java에 추가

    @Test
    @DisplayName("캘린더 인디케이터 정보를 조회하면 200 상태코드와 날짜 목록을 반환한다")
    void getScheduledDates_Success() throws Exception {
        // given
        int year = 2026;
        int month = 1;

        List<LocalDate> dates = List.of(
                LocalDate.of(2026, 1, 10),
                LocalDate.of(2026, 1, 15),
                LocalDate.of(2026, 1, 20),
                LocalDate.of(2026, 1, 25)
        );

        given(inviteCodeService.getScheduledDates(any(UUID.class), eq(year), eq(month)))
                .willReturn(dates);

        // when & then
        mockMvc.perform(get("/invite-code/calendar")
                        .param("year", String.valueOf(year))
                        .param("month", String.valueOf(month)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("등록 대기 중인 예약 날짜 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data.length()").value(4))
                .andExpect(jsonPath("$.data[0]").value("2026-01-10"))
                .andExpect(jsonPath("$.data[1]").value("2026-01-15"))
                .andExpect(jsonPath("$.data[2]").value("2026-01-20"))
                .andExpect(jsonPath("$.data[3]").value("2026-01-25"));
    }

    @Test
    @DisplayName("예약이 없는 월은 200 상태코드와 빈 배열을 반환한다")
    void getScheduledDates_EmptyResult() throws Exception {
        // given
        int year = 2026;
        int month = 12;

        given(inviteCodeService.getScheduledDates(any(UUID.class), eq(year), eq(month)))
                .willReturn(List.of());

        // when & then
        mockMvc.perform(get("/invite-code/calendar")
                        .param("year", String.valueOf(year))
                        .param("month", String.valueOf(month)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("등록 대기 중인 예약 날짜 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data.length()").value(0));
    }

    @Test
    @DisplayName("필수 파라미터가 누락되면 400 Bad Request를 반환한다 - 캘린더")
    void getScheduledDates_MissingParameter() throws Exception {
        // when & then - year만 있고 month 누락
        mockMvc.perform(get("/invite-code/calendar")
                        .param("year", "2026"))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("인증된 사용자의 병원 ID로 캘린더를 조회한다")
    void getScheduledDates_UsesAuthenticatedHospitalId() throws Exception {
        // given
        int year = 2026;
        int month = 1;

        given(inviteCodeService.getScheduledDates(eq(TEST_HOSPITAL_ID), eq(year), eq(month)))
                .willReturn(List.of());

        // when
        mockMvc.perform(get("/invite-code/calendar")
                        .param("year", String.valueOf(year))
                        .param("month", String.valueOf(month)))
                .andExpect(status().isOk());

        // then - 인증된 사용자의 병원 ID가 사용되었는지 검증
        verify(inviteCodeService, times(1))
                .getScheduledDates(eq(TEST_HOSPITAL_ID), eq(year), eq(month));
    }

    @Test
    @DisplayName("다양한 월에 대해 정상적으로 조회한다")
    void getScheduledDates_VariousMonths() throws Exception {
        // given - 2월
        given(inviteCodeService.getScheduledDates(any(UUID.class), eq(2026), eq(2)))
                .willReturn(List.of(LocalDate.of(2026, 2, 14)));

        // when & then - 2월
        mockMvc.perform(get("/invite-code/calendar")
                        .param("year", "2026")
                        .param("month", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data[0]").value("2026-02-14"));

        // given - 12월
        given(inviteCodeService.getScheduledDates(any(UUID.class), eq(2026), eq(12)))
                .willReturn(List.of(LocalDate.of(2026, 12, 25)));

        // when & then - 12월
        mockMvc.perform(get("/invite-code/calendar")
                        .param("year", "2026")
                        .param("month", "12"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data[0]").value("2026-12-25"));
    }
}