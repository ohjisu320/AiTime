package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus; // ✅ 너 프로젝트 패키지에 맞게 수정
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.hospital.dto.response.ChildResponse;
import com.ssafy.aitime.domain.hospital.dto.response.TotalPatientListResponse;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import com.ssafy.aitime.domain.hospital.repository.ReservationRepository;
import com.ssafy.aitime.domain.user.entity.User;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.mock;

@ExtendWith(MockitoExtension.class)
class DoctorServiceImplTest {

    @Mock ReservationRepository reservationRepository;
    @Mock HospitalChildrenRepository hospitalChildrenRepository;
    @Mock ChildRepository childRepository;
    @Mock ExamRepository examRepository;

    @InjectMocks DoctorServiceImpl doctorService;

    @Test
    @DisplayName("예약(취소 제외) -> ACTIVE 링크 -> ACTIVE child -> child별 최신 examStatus 매핑하여 반환")
    void getTotalPatientList_success_latestExamStatus() {
        // given
        UUID doctorId = UUID.randomUUID();

        // hospitalChildrenId 2개 (예약에서 가져온다고 가정)
        UUID hcId1 = UUID.randomUUID();
        UUID hcId2 = UUID.randomUUID();

        // childId 2개
        UUID childId1 = UUID.randomUUID();
        UUID childId2 = UUID.randomUUID();

        // User는 child.getUser().getUserId() 때문에 필요
        User user = mock(User.class);
        UUID userId = UUID.randomUUID();
        given(user.getUserId()).willReturn(userId);

        // Child 2개 (RecordStatus.ACTIVE)
        Child child1 = mock(Child.class);
        given(child1.getChildId()).willReturn(childId1);
        given(child1.getUser()).willReturn(user);
        given(child1.getName()).willReturn("아이1");
        given(child1.getBirthdate()).willReturn(LocalDate.now().minusMonths(18));
        given(child1.getGender()).willReturn(Gender.MALE);

        Child child2 = mock(Child.class);
        given(child2.getChildId()).willReturn(childId2);
        given(child2.getUser()).willReturn(user);
        given(child2.getName()).willReturn("아이2");
        given(child2.getBirthdate()).willReturn(LocalDate.now().minusMonths(20));
        given(child2.getGender()).willReturn(Gender.FEMALE);

        // Reservation -> hospitalChildrenId 추출 흐름
        Reservation r1 = mock(Reservation.class);
        Reservation r2 = mock(Reservation.class);

        HospitalChildren hc1 = mock(HospitalChildren.class);
        given(hc1.getHospitalChildrenId()).willReturn(hcId1);
        HospitalChildren hc2 = mock(HospitalChildren.class);
        given(hc2.getHospitalChildrenId()).willReturn(hcId2);

        given(r1.getHospitalChildren()).willReturn(hc1);
        given(r2.getHospitalChildren()).willReturn(hc2);

        given(reservationRepository.findByDoctorIdAndReservationStatusNot(doctorId, ReservationStatus.CANCELLED))
                .willReturn(List.of(r1, r2));

        // hospitalChildrenRepository -> HospitalChildren 엔티티 리스트 (ACTIVE)
        // 여기서 childId 추출함
        HospitalChildren hcEntity1 = mock(HospitalChildren.class);
        given(hcEntity1.getChild()).willReturn(child1);

        HospitalChildren hcEntity2 = mock(HospitalChildren.class);
        given(hcEntity2.getChild()).willReturn(child2);

        given(hospitalChildrenRepository.findByHospitalChildrenIdInAndLinkStatus(List.of(hcId1, hcId2), LinkStatus.ACTIVE))
                .willReturn(List.of(hcEntity1, hcEntity2));

        // childRepository -> Child 객체들
        given(childRepository.findByChildIdInAndRecordStatus(List.of(childId1, childId2), RecordStatus.ACTIVE))
                .willReturn(List.of(child1, child2));

        // examRepository -> childId들로 exam을 "completedAt desc"로 받는다고 가정
        // child1은 최신이 IN_PROGRESS, child2는 exam 없음
        Exam exam1_newest = mock(Exam.class);
        given(exam1_newest.getChild()).willReturn(child1);
        given(exam1_newest.getExamStatus()).willReturn(ExamStatus.IN_PROGRESS);

        Exam exam1_older = mock(Exam.class);
        given(exam1_older.getChild()).willReturn(child1);
        given(exam1_older.getExamStatus()).willReturn(ExamStatus.COMPLETED);

        given(examRepository.findByChild_ChildIdInOrderByCompletedAtDesc(List.of(childId1, childId2)))
                .willReturn(List.of(exam1_newest, exam1_older));

        // when
        TotalPatientListResponse res = doctorService.getTotalPatientList(doctorId);

        // then
        assertThat(res).isNotNull();
        assertThat(res.total()).isEqualTo(2L);

        List<ChildResponse> list = res.childResponses();
        assertThat(list).hasSize(2);

        // child1 최신 상태는 IN_PROGRESS
        ChildResponse cr1 = list.stream().filter(x -> x.childId().equals(childId1)).findFirst().orElseThrow();
        assertThat(cr1.latestExamStatus()).isEqualTo("IN_PROGRESS");
        assertThat(cr1.name()).isEqualTo("아이1");
        assertThat(cr1.userId()).isEqualTo(userId);

        // child2 exam 없음 -> "NONE"
        ChildResponse cr2 = list.stream().filter(x -> x.childId().equals(childId2)).findFirst().orElseThrow();
        assertThat(cr2.latestExamStatus()).isEqualTo("NONE");
    }

    @Test
    @DisplayName("예약이 없으면 빈 리스트/0 반환")
    void getTotalPatientList_empty_whenNoReservation() {
        // given
        UUID doctorId = UUID.randomUUID();

        given(reservationRepository.findByDoctorIdAndReservationStatusNot(doctorId, ReservationStatus.CANCELLED))
                .willReturn(Collections.emptyList());

        // 아래는 호출될 수도/안될 수도 있는데, 안전하게 빈 반환 세팅
        given(hospitalChildrenRepository.findByHospitalChildrenIdInAndLinkStatus(Collections.emptyList(), LinkStatus.ACTIVE))
                .willReturn(Collections.emptyList());
        given(childRepository.findByChildIdInAndRecordStatus(Collections.emptyList(), RecordStatus.ACTIVE))
                .willReturn(Collections.emptyList());
        given(examRepository.findByChild_ChildIdInOrderByCompletedAtDesc(Collections.emptyList()))
                .willReturn(Collections.emptyList());

        // when
        TotalPatientListResponse res = doctorService.getTotalPatientList(doctorId);

        // then
        assertThat(res.total()).isZero();
        assertThat(res.childResponses()).isEmpty();

    }
}
