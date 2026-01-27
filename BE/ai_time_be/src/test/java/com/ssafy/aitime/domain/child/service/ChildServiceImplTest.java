package com.ssafy.aitime.domain.child.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.dto.request.ChildCreateRequest;
import com.ssafy.aitime.domain.child.dto.request.ChildDeleteResponse;
import com.ssafy.aitime.domain.child.dto.response.ChildInfoResponse;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.child.exception.ChildAccessDeniedException;
import com.ssafy.aitime.domain.child.exception.ChildNotFoundException;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.service.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ChildServiceImplTest {
    @InjectMocks
    private ChildServiceImpl childService;

    @Mock
    private ChildRepository childRepository;

    @Mock
    private UserService userService;

    private User user;
    private final UUID userId = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        user = User.builder()
                .loginId("ssafy123")
                .name("김싸피")
                .build();
        ReflectionTestUtils.setField(user, "userId", userId);
    }

    @Test
    @DisplayName("새로운 아이를 등록하면 정확한 개월 수가 계산되어 반환된다")
    void addChild_Success() {
        // given
        // 현재 날짜 기준 10개월 전 날짜 설정
        LocalDate birthdate = LocalDate.now().minusMonths(10);
        ChildCreateRequest request = new ChildCreateRequest("박튼튼", birthdate, Gender.MALE);

        Child child = Child.builder()
                .user(user)
                .name(request.name())
                .birthdate(request.birthdate())
                .gender(request.gender())
                .build();
        ReflectionTestUtils.setField(child, "childId", UUID.randomUUID());

        given(userService.getById(userId)).willReturn(user);
        given(childRepository.save(any(Child.class))).willReturn(child);

        // when
        ChildInfoResponse response = childService.addChild(userId, request);

        // then
        assertThat(response.name()).isEqualTo("박튼튼");
        assertThat(response.months()).isEqualTo(10); // 10개월 차이 검증
        assertThat(response.gender()).isEqualTo(Gender.MALE);
        verify(childRepository, times(1)).save(any(Child.class));
    }

    @Test
    @DisplayName("아이 목록 조회 시 ACTIVE 상태인 아이들만 조회하고 개월 수를 계산한다")
    void getChildList_Success() {
        // given
        Child child1 = Child.builder().name("아이1").birthdate(LocalDate.now().minusMonths(5)).build();
        Child child2 = Child.builder().name("아이2").birthdate(LocalDate.now().minusMonths(15)).build();

        given(userService.getById(userId)).willReturn(user);
        given(childRepository.findByUser_UserIdAndRecordStatus(userId, RecordStatus.ACTIVE))
                .willReturn(List.of(child1, child2));

        // when
        List<ChildInfoResponse> result = childService.getChildList(userId);

        // then
        assertThat(result).hasSize(2);
        assertThat(result.get(0).months()).isEqualTo(5);
        assertThat(result.get(1).months()).isEqualTo(15);
        verify(childRepository, times(1)).findByUser_UserIdAndRecordStatus(userId, RecordStatus.ACTIVE);
    }

    @Test
    @DisplayName("아이 삭제 시 본인의 아이가 아니면 ChildAccessDeniedException이 발생한다")
    void deleteChild_Fail_AccessDenied() {
        // given
        UUID otherUserId = UUID.randomUUID();
        User otherUser = User.builder().build();
        ReflectionTestUtils.setField(otherUser, "userId", otherUserId);

        UUID childId = UUID.randomUUID();
        Child child = Child.builder()
                .user(otherUser) // 소유자가 다른 유저
                .build();

        given(userService.getById(userId)).willReturn(user);
        given(childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE))
                .willReturn(Optional.of(child));

        // when & then
        assertThatThrownBy(() -> childService.deleteChild(userId, childId))
                .isInstanceOf(ChildAccessDeniedException.class);

        verify(childRepository, never()).delete(any());
    }

    @Test
    @DisplayName("존재하지 않거나 이미 삭제된 아이를 삭제하려 하면 ChildNotFoundException이 발생한다")
    void deleteChild_Fail_NotFound() {
        // given
        UUID childId = UUID.randomUUID();
        given(userService.getById(userId)).willReturn(user);
        given(childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE))
                .willReturn(Optional.empty());

        // when & then
        assertThatThrownBy(() -> childService.deleteChild(userId, childId))
                .isInstanceOf(ChildNotFoundException.class);
    }

    @Test
    @DisplayName("정상적인 삭제 요청 시 repository.delete가 호출된다")
    void deleteChild_Success() {
        // given
        UUID childId = UUID.randomUUID();
        Child child = Child.builder()
                .user(user) // 소유자가 본인
                .build();

        given(userService.getById(userId)).willReturn(user);
        given(childRepository.findByChildIdAndRecordStatus(childId, RecordStatus.ACTIVE))
                .willReturn(Optional.of(child));

        // when
        ChildDeleteResponse response = childService.deleteChild(userId, childId);

        // then
        assertThat(response.childId()).isEqualTo(childId);
        assertThat(response.status()).isEqualTo(RecordStatus.DELETED);
        verify(childRepository, times(1)).delete(child);
    }
}