package com.ssafy.aitime.domain.hospital.repository;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.user.entity.User;
import jakarta.persistence.EntityManager;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@DisplayName("HospitalChildrenRepository 테스트")
class HospitalChildrenRepositoryTest {

    @Autowired
    private HospitalChildrenRepository hospitalChildrenRepository;

    @Autowired
    private EntityManager em;

    @Test
    @DisplayName("hospitalChildrenIds + LinkStatus.ACTIVE 조건으로 HospitalChildren 엔티티만 조회된다")
    void findByHospitalChildrenIdInAndLinkStatus_ActiveOnly() {
        // given
        User user = persistUser();
        Hospital hospital = persistHospital("HOSP-001", "서울아동병원", "서울특별시", "02-1234-5678", RecordStatus.ACTIVE);

        Child child1 = persistChild(user, "홍길동", LocalDate.of(2023, 1, 15), Gender.MALE, RecordStatus.ACTIVE);
        Child child2 = persistChild(user, "김철수", LocalDate.of(2023, 3, 20), Gender.MALE, RecordStatus.ACTIVE);

        HospitalChildren hcActive = persistHospitalChildren(child1, hospital, LinkStatus.ACTIVE);
        HospitalChildren hcInactive = persistHospitalChildren(child2, hospital, LinkStatus.INACTIVE);

        em.flush();
        em.clear();

        List<UUID> hospitalChildrenIds = Arrays.asList(
                hcActive.getHospitalChildrenId(),
                hcInactive.getHospitalChildrenId()
        );

        // when
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(hospitalChildrenIds, LinkStatus.ACTIVE);

        // then
        assertThat(result).hasSize(1);

        HospitalChildren found = result.get(0);
        assertThat(found.getHospitalChildrenId()).isEqualTo(hcActive.getHospitalChildrenId());
        assertThat(found.getLinkStatus()).isEqualTo(LinkStatus.ACTIVE);
        assertThat(found.getChild().getChildId()).isEqualTo(child1.getChildId());
    }

    @Test
    @DisplayName("hospitalChildrenIds + LinkStatus.INACTIVE 조건으로 INACTIVE 데이터만 조회된다")
    void findByHospitalChildrenIdInAndLinkStatus_InactiveOnly() {
        // given
        User user = persistUser();
        Hospital hospital = persistHospital("HOSP-002", "부산아동병원", "부산광역시", "051-9876-5432", RecordStatus.ACTIVE);

        Child child1 = persistChild(user, "이영희", LocalDate.of(2023, 5, 10), Gender.FEMALE, RecordStatus.ACTIVE);
        Child child2 = persistChild(user, "박민수", LocalDate.of(2023, 7, 25), Gender.MALE, RecordStatus.ACTIVE);

        HospitalChildren hcActive = persistHospitalChildren(child1, hospital, LinkStatus.ACTIVE);
        HospitalChildren hcInactive = persistHospitalChildren(child2, hospital, LinkStatus.INACTIVE);

        em.flush();
        em.clear();

        List<UUID> hospitalChildrenIds = Arrays.asList(
                hcActive.getHospitalChildrenId(),
                hcInactive.getHospitalChildrenId()
        );

        // when
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(hospitalChildrenIds, LinkStatus.INACTIVE);

        // then
        assertThat(result).hasSize(1);

        HospitalChildren found = result.get(0);
        assertThat(found.getHospitalChildrenId()).isEqualTo(hcInactive.getHospitalChildrenId());
        assertThat(found.getLinkStatus()).isEqualTo(LinkStatus.INACTIVE);
        assertThat(found.getChild().getChildId()).isEqualTo(child2.getChildId());
    }

    @Test
    @DisplayName("여러 ACTIVE 상태 데이터가 모두 조회된다")
    void findByHospitalChildrenIdInAndLinkStatus_MultipleActive() {
        // given
        User user = persistUser();
        Hospital hospital = persistHospital("HOSP-003", "대전아동병원", "대전광역시", "042-5555-6666", RecordStatus.ACTIVE);

        Child child1 = persistChild(user, "최지훈", LocalDate.of(2023, 2, 5), Gender.MALE, RecordStatus.ACTIVE);
        Child child2 = persistChild(user, "정수아", LocalDate.of(2023, 4, 15), Gender.FEMALE, RecordStatus.ACTIVE);
        Child child3 = persistChild(user, "강민지", LocalDate.of(2023, 6, 20), Gender.FEMALE, RecordStatus.ACTIVE);

        HospitalChildren hc1 = persistHospitalChildren(child1, hospital, LinkStatus.ACTIVE);
        HospitalChildren hc2 = persistHospitalChildren(child2, hospital, LinkStatus.ACTIVE);
        HospitalChildren hc3 = persistHospitalChildren(child3, hospital, LinkStatus.INACTIVE);

        em.flush();
        em.clear();

        List<UUID> hospitalChildrenIds = Arrays.asList(
                hc1.getHospitalChildrenId(),
                hc2.getHospitalChildrenId(),
                hc3.getHospitalChildrenId()
        );

        // when
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(hospitalChildrenIds, LinkStatus.ACTIVE);

        // then
        assertThat(result).hasSize(2);
        assertThat(result).extracting(HospitalChildren::getHospitalChildrenId)
                .containsExactlyInAnyOrder(
                        hc1.getHospitalChildrenId(),
                        hc2.getHospitalChildrenId()
                );
        assertThat(result).allMatch(hc -> hc.getLinkStatus() == LinkStatus.ACTIVE);
    }

    @Test
    @DisplayName("조건에 해당하는 데이터가 없으면 빈 리스트")
    void findByHospitalChildrenIdInAndLinkStatus_Empty() {
        // when
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(
                        Collections.singletonList(UUID.randomUUID()),
                        LinkStatus.ACTIVE
                );

        // then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("빈 ID 목록으로 조회 시 빈 리스트 반환")
    void findByHospitalChildrenIdInAndLinkStatus_EmptyIdList() {
        // when
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(
                        Collections.emptyList(),
                        LinkStatus.ACTIVE
                );

        // then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("존재하는 ID지만 다른 LinkStatus로 조회 시 빈 리스트")
    void findByHospitalChildrenIdInAndLinkStatus_DifferentStatus() {
        // given
        User user = persistUser();
        Hospital hospital = persistHospital("HOSP-004", "광주아동병원", "광주광역시", "062-7777-8888", RecordStatus.ACTIVE);

        Child child = persistChild(user, "송하늘", LocalDate.of(2023, 8, 10), Gender.MALE, RecordStatus.ACTIVE);
        HospitalChildren hcActive = persistHospitalChildren(child, hospital, LinkStatus.ACTIVE);

        em.flush();
        em.clear();

        // when - ACTIVE 데이터를 INACTIVE 상태로 조회
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(
                        Collections.singletonList(hcActive.getHospitalChildrenId()),
                        LinkStatus.INACTIVE
                );

        // then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("중복된 ID가 있어도 결과는 중복 없이 반환된다")
    void findByHospitalChildrenIdInAndLinkStatus_DuplicateIds() {
        // given
        User user = persistUser();
        Hospital hospital = persistHospital("HOSP-006", "울산아동병원", "울산광역시", "052-3333-4444", RecordStatus.ACTIVE);

        Child child = persistChild(user, "한지원", LocalDate.of(2023, 11, 20), Gender.FEMALE, RecordStatus.ACTIVE);
        HospitalChildren hc = persistHospitalChildren(child, hospital, LinkStatus.ACTIVE);

        em.flush();
        em.clear();

        // 같은 ID를 여러 번 포함
        List<UUID> duplicateIds = Arrays.asList(
                hc.getHospitalChildrenId(),
                hc.getHospitalChildrenId(),
                hc.getHospitalChildrenId()
        );

        // when
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(duplicateIds, LinkStatus.ACTIVE);

        // then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getHospitalChildrenId()).isEqualTo(hc.getHospitalChildrenId());
    }

    @Test
    @DisplayName("여러 병원의 환자 데이터가 섞여 있어도 정확히 필터링된다")
    void findByHospitalChildrenIdInAndLinkStatus_MultipleHospitals() {
        // given
        User user = persistUser();
        Hospital hospital1 = persistHospital("HOSP-007", "서울병원", "서울특별시", "02-1111-2222", RecordStatus.ACTIVE);
        Hospital hospital2 = persistHospital("HOSP-008", "부산병원", "부산광역시", "051-3333-4444", RecordStatus.ACTIVE);

        Child child1 = persistChild(user, "권태양", LocalDate.of(2023, 12, 1), Gender.MALE, RecordStatus.ACTIVE);
        Child child2 = persistChild(user, "오별", LocalDate.of(2024, 1, 5), Gender.FEMALE, RecordStatus.ACTIVE);

        HospitalChildren hc1 = persistHospitalChildren(child1, hospital1, LinkStatus.ACTIVE);
        HospitalChildren hc2 = persistHospitalChildren(child2, hospital2, LinkStatus.ACTIVE);

        em.flush();
        em.clear();

        List<UUID> hospitalChildrenIds = Arrays.asList(
                hc1.getHospitalChildrenId(),
                hc2.getHospitalChildrenId()
        );

        // when
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(hospitalChildrenIds, LinkStatus.ACTIVE);

        // then
        assertThat(result).hasSize(2);
        assertThat(result).extracting(HospitalChildren::getHospitalChildrenId)
                .containsExactlyInAnyOrder(
                        hc1.getHospitalChildrenId(),
                        hc2.getHospitalChildrenId()
                );
    }

    // ----------------- helpers -----------------

    private User persistUser() {
        User user = User.builder()
                .loginId("test_" + UUID.randomUUID())
                .password("password123")
                .name("테스트유저")
                .build();
        em.persist(user);
        return user;
    }

    private Hospital persistHospital(String code, String name, String address, String phoneNumber, RecordStatus status) {
        Hospital hospital = Hospital.builder()
                .hospitalCode(code)
                .name(name)
                .address(address)
                .phoneNumber(phoneNumber)  // phoneNumber 추가
                .recordStatus(status)
                .build();
        em.persist(hospital);
        return hospital;
    }

    private Child persistChild(User user, String name, LocalDate birthdate, Gender gender, RecordStatus status) {
        Child child = Child.builder()
                .user(user)
                .name(name)
                .birthdate(birthdate)
                .gender(gender)
                .recordStatus(status)
                .build();
        em.persist(child);
        return child;
    }

    private HospitalChildren persistHospitalChildren(Child child, Hospital hospital, LinkStatus linkStatus) {
        HospitalChildren hc = HospitalChildren.builder()
                .child(child)
                .hospital(hospital)
                .linkStatus(linkStatus)
                .build();
        em.persist(hc);
        return hc;
    }
}