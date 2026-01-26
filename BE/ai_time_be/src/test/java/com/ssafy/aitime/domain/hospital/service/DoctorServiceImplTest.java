package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender; // ✅ 만약 패키지/이름 다르면 너 프로젝트 enum에 맞게 수정
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.PatientSearchResponse;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.exception.DoctorNotFoundException;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import com.ssafy.aitime.domain.hospital.repository.HospitalStaffRepository;
import com.ssafy.aitime.domain.hospital.repository.ReservationRepository;
import com.ssafy.aitime.domain.user.entity.User;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Method;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DoctorServiceImplTest {

    @Mock private ReservationRepository reservationRepository;
    @Mock private HospitalChildrenRepository hospitalChildrenRepository;
    @Mock private HospitalStaffRepository hospitalStaffRepository;
    @Mock private ChildRepository childRepository;
    @Mock private ExamRepository examRepository;

    @InjectMocks
    private DoctorServiceImpl doctorService;

    @Test
    void getSearchPatientList_withDateFilter_returnsPatients() {
        // given
        UUID doctorId = UUID.randomUUID();

        PatientSearchRequest req = mock(PatientSearchRequest.class);
        LocalDate filterDate = LocalDate.of(2026, 1, 26);
        LocalDateTime startOfDay = filterDate.atStartOfDay();
        LocalDateTime endOfDay = filterDate.plusDays(1).atStartOfDay();

        given(req.getEffectiveDate()).willReturn(filterDate);
        given(req.hasNameFilter()).willReturn(false);
        given(req.hasResultStatusFilter()).willReturn(false);
        given(req.page()).willReturn(0);
        given(req.size()).willReturn(10);

        // doctor validation
        given(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                eq(doctorId), eq(StaffRole.DOCTOR), eq(RecordStatus.ACTIVE)
        )).willReturn(true);

        // reservations -> hospitalChildrenIds
        UUID hcId1 = UUID.randomUUID();
        UUID hcId2 = UUID.randomUUID();

        Reservation r1 = mockReservation(hcId1);
        Reservation r2 = mockReservation(hcId1); // 중복
        Reservation r3 = mockReservation(hcId2);

        given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                eq(doctorId), eq(ReservationStatus.CANCELLED), eq(startOfDay), eq(endOfDay)
        )).willReturn(List.of(r1, r2, r3));

        // hospital_children -> childIds
        UUID childId1 = UUID.randomUUID();
        UUID childId2 = UUID.randomUUID();

        HospitalChildren hc1 = mockHospitalChildren(hcId1, childId1);
        HospitalChildren hc2 = mockHospitalChildren(hcId2, childId2);

        given(hospitalChildrenRepository.findByHospitalChildrenIdInAndLinkStatus(
                argThat(list -> list.containsAll(List.of(hcId1, hcId2))), eq(LinkStatus.ACTIVE)
        )).willReturn(List.of(hc1, hc2));

        // children
        UUID userId1 = UUID.randomUUID();
        UUID userId2 = UUID.randomUUID();

        Child c1 = mockChild(childId1, userId1, "홍길동", LocalDate.of(2015, 5, 20), Gender.MALE);
        Child c2 = mockChild(childId2, userId2, "김철수", LocalDate.of(2016, 6, 10), Gender.FEMALE);

        given(childRepository.findByChildIdInAndRecordStatus(
                argThat(list -> list.containsAll(List.of(childId1, childId2))), eq(RecordStatus.ACTIVE)
        )).willReturn(List.of(c1, c2));

        // exams 비워두면 latestExamStatus = "NONE"
        given(examRepository.findByChild_ChildIdInOrderByCompletedAtDesc(anyList()))
                .willReturn(Collections.emptyList());

        // when
        PatientSearchResponse resp = doctorService.getSearchPatientList(doctorId, req);

        // then (반환값은 DTO가 record/class 어느 쪽이든 동작하게 reflection으로 검증)
        List<?> items = extractList(resp);
        int total = extractTotal(resp);

        assertThat(items).hasSize(2);
        assertThat(total).isEqualTo(2);

        // date 필터 경로로 호출됐는지 확인
        verify(reservationRepository, times(1))
                .findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(
                        eq(doctorId), eq(ReservationStatus.CANCELLED), eq(startOfDay), eq(endOfDay)
                );
        verify(reservationRepository, never())
                .findByDoctorIdAndReservationStatusNot(eq(doctorId), eq(ReservationStatus.CANCELLED));
    }

    @Test
    void getSearchPatientList_noDateFilter_withNameFilter_andPaging() {
        // given
        UUID doctorId = UUID.randomUUID();

        PatientSearchRequest req = mock(PatientSearchRequest.class);
        given(req.getEffectiveDate()).willReturn(null);

        given(req.hasNameFilter()).willReturn(true);
        given(req.name()).willReturn("길"); // "홍길동"만 남게
        given(req.hasResultStatusFilter()).willReturn(false);

        given(req.page()).willReturn(0);
        given(req.size()).willReturn(1); // 페이징으로 1개만

        given(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                eq(doctorId), eq(StaffRole.DOCTOR), eq(RecordStatus.ACTIVE)
        )).willReturn(true);

        UUID hcId1 = UUID.randomUUID();
        UUID hcId2 = UUID.randomUUID();

        Reservation r1 = mockReservation(hcId1);
        Reservation r2 = mockReservation(hcId2);

        given(reservationRepository.findByDoctorIdAndReservationStatusNot(
                eq(doctorId), eq(ReservationStatus.CANCELLED)
        )).willReturn(List.of(r1, r2));

        UUID childId1 = UUID.randomUUID();
        UUID childId2 = UUID.randomUUID();

        HospitalChildren hc1 = mockHospitalChildren(hcId1, childId1);
        HospitalChildren hc2 = mockHospitalChildren(hcId2, childId2);

        given(hospitalChildrenRepository.findByHospitalChildrenIdInAndLinkStatus(anyList(), eq(LinkStatus.ACTIVE)))
                .willReturn(List.of(hc1, hc2));

        Child c1 = mockChild(childId1, UUID.randomUUID(), "홍길동", LocalDate.of(2015, 5, 20), Gender.MALE);
        Child c2 = mockChild(childId2, UUID.randomUUID(), "김철수", LocalDate.of(2016, 6, 10), Gender.MALE);

        given(childRepository.findByChildIdInAndRecordStatus(anyList(), eq(RecordStatus.ACTIVE)))
                .willReturn(List.of(c1, c2));

        given(examRepository.findByChild_ChildIdInOrderByCompletedAtDesc(anyList()))
                .willReturn(Collections.emptyList()); // NONE

        // when
        PatientSearchResponse resp = doctorService.getSearchPatientList(doctorId, req);

        // then
        List<?> items = extractList(resp);
        int total = extractTotal(resp);

        // 이름 필터 후 총 1명, 페이지 size=1이라 items도 1명
        assertThat(total).isEqualTo(1);
        assertThat(items).hasSize(1);

        // no-date 경로 호출 확인
        verify(reservationRepository, times(1))
                .findByDoctorIdAndReservationStatusNot(eq(doctorId), eq(ReservationStatus.CANCELLED));
        verify(reservationRepository, never())
                .findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(any(), any(), any(), any());
    }

    @Test
    void getSearchPatientList_doctorNotFound_throws() {
        // given
        UUID doctorId = UUID.randomUUID();
        PatientSearchRequest req = mock(PatientSearchRequest.class);

        given(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(
                eq(doctorId), eq(StaffRole.DOCTOR), eq(RecordStatus.ACTIVE)
        )).willReturn(false);

        // when & then
        assertThatThrownBy(() -> doctorService.getSearchPatientList(doctorId, req))
                .isInstanceOf(DoctorNotFoundException.class);

        verifyNoInteractions(reservationRepository);
        verifyNoInteractions(hospitalChildrenRepository);
        verifyNoInteractions(childRepository);
        verifyNoInteractions(examRepository);
    }

    // ---------------- helpers ----------------

    private static Reservation mockReservation(UUID hospitalChildrenId) {
        Reservation r = mock(Reservation.class);
        HospitalChildren hc = mock(HospitalChildren.class);
        given(hc.getHospitalChildrenId()).willReturn(hospitalChildrenId);
        given(r.getHospitalChildren()).willReturn(hc);
        return r;
    }

    private static HospitalChildren mockHospitalChildren(UUID childId) {
        HospitalChildren hc = mock(HospitalChildren.class);
        Child child = mock(Child.class);

        given(child.getChildId()).willReturn(childId);
        given(hc.getChild()).willReturn(child);

        // ✅ 아래 stubbing은 서비스에서 안 써서 UnnecessaryStubbingException 유발 가능
        // given(hc.getHospitalChildrenId()).willReturn(hospitalChildrenId);

        return hc;
    }


    private static Child mockChild(UUID childId, UUID userId, String name, LocalDate birthdate, Gender gender) {
        Child child = mock(Child.class);
        User user = mock(User.class);

        given(user.getUserId()).willReturn(userId);

        given(child.getChildId()).willReturn(childId);
        given(child.getUser()).willReturn(user);
        given(child.getName()).willReturn(name);
        given(child.getBirthdate()).willReturn(birthdate);
        given(child.getGender()).willReturn(gender);

        return child;
    }

    @SuppressWarnings("unchecked")
    private static List<?> extractList(Object resp) {
        // 1) 흔한 이름 후보 먼저 시도
        for (String m : List.of(
                "items", "getItems",
                "children", "getChildren",
                "patientList", "getPatientList",
                "responses", "getResponses",
                "data", "getData"
        )) {
            Object v = tryInvoke(resp, m);
            if (v instanceof List) return (List<?>) v;
        }

        // 2) 이름 몰라도 OK: "인자 없고 List 반환" public 메서드 탐색
        Method candidate = Arrays.stream(resp.getClass().getMethods())
                .filter(m -> m.getParameterCount() == 0)
                .filter(m -> List.class.isAssignableFrom(m.getReturnType()))
                .findFirst()
                .orElse(null);

        if (candidate == null) {
            String methods = Arrays.stream(resp.getClass().getMethods())
                    .filter(m -> m.getDeclaringClass() != Object.class)
                    .map(m -> m.getName() + " : " + m.getReturnType().getSimpleName())
                    .distinct()
                    .sorted()
                    .reduce("", (a, b) -> a + "\n- " + b);

            fail("PatientSearchResponse에서 List 반환 메서드를 못 찾았어. 발견된 메서드:" + methods);
        }

        try {
            Object v = candidate.invoke(resp);
            if (v instanceof List) return (List<?>) v;
            fail("List 반환 메서드로 보였는데 실제 반환이 List가 아니야: " + candidate.getName());
            return List.of();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private static int extractTotal(Object resp) {
        // 1) 흔한 이름 후보 먼저 시도
        for (String m : List.of(
                "total", "getTotal",
                "count", "getCount",
                "totalCount", "getTotalCount"
        )) {
            Object v = tryInvoke(resp, m);
            Integer parsed = toInt(v);
            if (parsed != null) return parsed;
        }

        // 2) 이름 몰라도 OK: "인자 없고 숫자 반환" public 메서드 탐색
        Method candidate = Arrays.stream(resp.getClass().getMethods())
                .filter(m -> m.getParameterCount() == 0)
                .filter(m -> {
                    Class<?> rt = m.getReturnType();
                    return rt == int.class || rt == Integer.class || rt == long.class || rt == Long.class;
                })
                .findFirst()
                .orElse(null);

        if (candidate == null) {
            String methods = Arrays.stream(resp.getClass().getMethods())
                    .filter(m -> m.getDeclaringClass() != Object.class)
                    .map(m -> m.getName() + " : " + m.getReturnType().getSimpleName())
                    .distinct()
                    .sorted()
                    .reduce("", (a, b) -> a + "\n- " + b);

            fail("PatientSearchResponse에서 total/count 반환 메서드를 못 찾았어. 발견된 메서드:" + methods);
        }

        try {
            Object v = candidate.invoke(resp);
            Integer parsed = toInt(v);
            if (parsed != null) return parsed;
            fail("total 반환 메서드로 보였는데 int로 변환이 안돼: " + candidate.getName());
            return 0;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private static Integer toInt(Object v) {
        if (v instanceof Integer i) return i;
        if (v instanceof Long l) return Math.toIntExact(l);
        if (v instanceof Short s) return (int) s;
        return null;
    }

    private static Object tryInvoke(Object target, String methodName) {
        try {
            Method m = target.getClass().getMethod(methodName);
            return m.invoke(target);
        } catch (Exception ignored) {
            return null;
        }
    }
}
