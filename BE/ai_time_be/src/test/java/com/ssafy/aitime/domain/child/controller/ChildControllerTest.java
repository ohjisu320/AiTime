package com.ssafy.aitime.domain.child.controller;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.request.ChildDeleteResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildInfoResponse;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.child.service.ChildService;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.security.principal.UserPrincipal;
import io.lettuce.core.dynamic.support.MethodParameter;
import org.jspecify.annotations.Nullable;
import org.junit.jupiter.api.BeforeEach;
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
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ChildController.class)
@AutoConfigureMockMvc(addFilters = false)
class ChildControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ChildService childService;

    @Autowired
    private ObjectMapper objectMapper;

    // 테스트에서 공통으로 사용할 고정 유저 ID
    private static final UUID TEST_USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000000");

    /**
     * @AuthenticationPrincipal UserPrincipal 에 가짜 객체를 주입하기 위한 설정
     */
    @TestConfiguration
    static class TestConfig implements WebMvcConfigurer {
        @Override
        public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
            resolvers.add(new HandlerMethodArgumentResolver() {
                @Override
                public boolean supportsParameter(org.springframework.core.MethodParameter parameter) {
                    return parameter.getParameterType().isAssignableFrom(UserPrincipal.class);
                }

                @Override
                public @Nullable Object resolveArgument(org.springframework.core.MethodParameter parameter, @Nullable ModelAndViewContainer mavContainer, NativeWebRequest webRequest, @Nullable WebDataBinderFactory binderFactory) throws Exception {
                    // 유효한 User 엔티티를 만들어 UserPrincipal 생성
                    User user = User.builder()
                            .loginId("testUser")
                            .userRole(UserRole.USER)
                            .recordStatus(RecordStatus.ACTIVE)
                            .build();
                    ReflectionTestUtils.setField(user, "userId", TEST_USER_ID);
                    return UserPrincipal.from(user);
                }
            });
        }
    }

    @Test
    @DisplayName("새로운 아이를 등록하면 201 상태코드와 등록 정보를 반환한다")
    void addChild_Success() throws Exception {
        // given
        ChildCreateRequest request = new ChildCreateRequest("박튼튼", LocalDate.of(2024, 5, 20), Gender.MALE);
        ChildInfoResponse response = new ChildInfoResponse(UUID.randomUUID(), "박튼튼", 20L, Gender.MALE);

        given(childService.addChild(any(UUID.class), any(ChildCreateRequest.class))).willReturn(response);

        // when & then
        mockMvc.perform(post("/child")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.message").value("아이 등록이 완료되었습니다."))
                .andExpect(jsonPath("$.data.name").value("박튼튼"))
                .andExpect(jsonPath("$.data.months").value(20));
    }

    @Test
    @DisplayName("현재 로그인한 유저의 아이 목록을 조회한다")
    void getChildren_Success() throws Exception {
        // given
        ChildInfoResponse child1 = new ChildInfoResponse(UUID.randomUUID(), "김행복", 18L, Gender.MALE);
        ChildInfoResponse child2 = new ChildInfoResponse(UUID.randomUUID(), "이사랑", 12L, Gender.FEMALE);

        given(childService.getChildList(any(UUID.class))).willReturn(List.of(child1, child2));

        // when & then
        mockMvc.perform(get("/child"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("아이 목록 조회가 완료되었습니다."))
                .andExpect(jsonPath("$.data[0].name").value("김행복"))
                .andExpect(jsonPath("$.data[1].name").value("이사랑"));
    }

    @Test
    @DisplayName("아이 정보를 삭제하면 200 상태코드와 삭제된 ID를 반환한다")
    void deleteChild_Success() throws Exception {
        // given
        UUID childId = UUID.randomUUID();
        ChildDeleteResponse response = new ChildDeleteResponse(childId, RecordStatus.DELETED);

        given(childService.deleteChild(any(UUID.class), any(UUID.class))).willReturn(response);

        // when & then
        mockMvc.perform(delete("/child/{childId}", childId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("아이 정보가 성공적으로 삭제되었습니다."))
                .andExpect(jsonPath("$.data.childId").value(childId.toString()))
                .andExpect(jsonPath("$.data.status").value("DELETED"));
    }
}