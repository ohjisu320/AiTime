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
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class HospitalChildrenRepositoryTest {

    @Autowired
    HospitalChildrenRepository hospitalChildrenRepository;

    @Autowired
    EntityManager em;

    @Test
    @DisplayName("hospitalChildrenIds + LinkStatus.ACTIVE 조건으로 HospitalChildren 엔티티만 조회된다")
    void findByHospitalChildrenIdInAndLinkStatus_activeOnly() {
        // given
        User user = persistUser();

        Child child1 = persistChild(user, "아이1", LocalDate.of(2024, 1, 1), Gender.MALE, RecordStatus.ACTIVE);
        Child child2 = persistChild(user, "아이2", LocalDate.of(2024, 2, 1), Gender.FEMALE, RecordStatus.ACTIVE);

        Hospital hospital = persistHospital("HOSP-" + UUID.randomUUID(), "병원A", "서울", RecordStatus.ACTIVE);

        HospitalChildren hcActive = persistHospitalChildren(child1, hospital, LinkStatus.ACTIVE);
        HospitalChildren hcInactive = persistHospitalChildren(child2, hospital, LinkStatus.INACTIVE);

        em.flush();
        em.clear();

        List<UUID> hospitalChildrenIds = List.of(
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

        // childId까지 같이 검증하고 싶으면
        assertThat(found.getChild().getChildId()).isEqualTo(child1.getChildId());
        assertThat(found.getChild().getChildId()).isNotEqualTo(child2.getChildId());
    }

    @Test
    @DisplayName("조건에 해당하는 데이터가 없으면 빈 리스트")
    void findByHospitalChildrenIdInAndLinkStatus_empty() {
        // when
        List<HospitalChildren> result = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(List.of(UUID.randomUUID()), LinkStatus.ACTIVE);

        // then
        assertThat(result).isEmpty();
    }

    // ----------------- helpers -----------------

    private Hospital persistHospital(String code, String name, String address, RecordStatus status) {
        Hospital hospital = Hospital.builder()
                .hospitalCode(code)
                .name(name)
                .address(address)
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

    /**
     * User 엔티티 필수값(예: loginId, password, name 등)에 맞춰 최소값만 채워주세요.
     * 아래는 로그에서 보이던 NOT NULL 제약(login_id 등)을 만족하도록 넣어둔 예시입니다.
     */
    private User persistUser() {
        User user = User.builder()
                .loginId("test_" + UUID.randomUUID())
                .password("pw")
                .name("테스트유저")
                .build();
        em.persist(user);
        return user;
    }
}
