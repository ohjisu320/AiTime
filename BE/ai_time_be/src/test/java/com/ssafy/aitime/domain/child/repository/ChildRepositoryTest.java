package com.ssafy.aitime.domain.child.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.user.entity.User;
import com.ssafy.aitime.domain.user.entity.enums.UserRole;
import com.ssafy.aitime.domain.user.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class ChildRepositoryTest {
    @Autowired
    private ChildRepository childRepository;

    @Autowired
    private UserRepository userRepository;

    private User savedUser;

    @BeforeEach
    void setUp() {
        // Child 엔티티 저장 시 필수인 User(부모) 엔티티를 먼저 생성하고 저장합니다.
        User user = User.builder()
                .loginId("parent123")
                .password("password!")
                .name("테스트부모")
                .userRole(UserRole.USER)
                .recordStatus(RecordStatus.ACTIVE)
                .build();
        savedUser = userRepository.save(user);
    }

    @Test
    @DisplayName("부모 ID와 ACTIVE 상태로 등록된 아이 목록을 조회한다")
    void findByUser_UserIdAndRecordStatus_Success() {
        // given
        Child child1 = Child.builder()
                .user(savedUser)
                .name("첫째")
                .birthdate(LocalDate.of(2023, 1, 1))
                .gender(Gender.MALE)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        Child child2 = Child.builder()
                .user(savedUser)
                .name("둘째")
                .birthdate(LocalDate.of(2025, 1, 1))
                .gender(Gender.FEMALE)
                .recordStatus(RecordStatus.ACTIVE)
                .build();

        childRepository.save(child1);
        childRepository.save(child2);

        // when
        List<Child> activeChildren = childRepository.findByUser_UserIdAndRecordStatus(savedUser.getUserId(), RecordStatus.ACTIVE);

        // then
        assertThat(activeChildren).hasSize(2);
        assertThat(activeChildren).extracting("name").containsExactlyInAnyOrder("첫째", "둘째");
    }

    @Test
    @DisplayName("여러 아이 ID 목록 중 ACTIVE 상태인 데이터만 필터링하여 조회한다")
    void findByChildIdInAndRecordStatus_Success() {
        // given
        Child child1 = childRepository.save(Child.builder()
                .user(savedUser)
                .name("활동중아이")
                .birthdate(LocalDate.now())
                .gender(Gender.MALE)
                .recordStatus(RecordStatus.ACTIVE)
                .build());

        Child child2 = childRepository.save(Child.builder()
                .user(savedUser)
                .name("삭제된아이")
                .birthdate(LocalDate.now())
                .gender(Gender.FEMALE)
                .recordStatus(RecordStatus.DELETED)
                .build());

        List<UUID> childIds = List.of(child1.getChildId(), child2.getChildId());

        // when
        List<Child> foundChildren = childRepository.findByChildIdInAndRecordStatus(childIds, RecordStatus.ACTIVE);

        // then
        assertThat(foundChildren).hasSize(1);
        assertThat(foundChildren.get(0).getName()).isEqualTo("활동중아이");
    }

    @Test
    @DisplayName("아이 ID와 ACTIVE 상태로 특정 아이를 단건 조회한다")
    void findByChildIdAndRecordStatus_Success() {
        // given
        Child child = Child.builder()
                .user(savedUser)
                .name("우리애기")
                .birthdate(LocalDate.of(2024, 10, 10))
                .gender(Gender.FEMALE)
                .recordStatus(RecordStatus.ACTIVE)
                .build();
        Child savedChild = childRepository.save(child);

        // when
        Optional<Child> foundChild = childRepository.findByChildIdAndRecordStatus(savedChild.getChildId(), RecordStatus.ACTIVE);

        // then
        assertThat(foundChild).isPresent();
        assertThat(foundChild.get().getName()).isEqualTo("우리애기");
        assertThat(foundChild.get().getRecordStatus()).isEqualTo(RecordStatus.ACTIVE);
    }

    @Test
    @DisplayName("아이 상태가 DELETED인 경우 ACTIVE 조건으로 조회 시 검색되지 않아야 한다")
    void findByChildIdAndRecordStatus_Fail_WhenDeleted() {
        // given
        Child child = Child.builder()
                .user(savedUser)
                .name("탈퇴아이")
                .birthdate(LocalDate.now())
                .gender(Gender.MALE)
                .recordStatus(RecordStatus.DELETED)
                .build();
        Child savedChild = childRepository.save(child);

        // when
        Optional<Child> foundChild = childRepository.findByChildIdAndRecordStatus(savedChild.getUser().getUserId(), RecordStatus.ACTIVE);

        // then
        assertThat(foundChild).isEmpty();
    }
}