package com.ssafy.aitime.domain.invite.controller;

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
import static org.mockito.BDDMockito.given;
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
}