package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.entity.enums.Gender;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.dto.response.AdosDetailResponse;
import com.ssafy.aitime.domain.exam.dto.response.ExamWithVideosResponse;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.enums.ExamStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import com.ssafy.aitime.domain.exam.service.ExamService;
import com.ssafy.aitime.domain.exam.service.VideoService;
import com.ssafy.aitime.domain.hospital.dto.request.PatientSearchRequest;
import com.ssafy.aitime.domain.hospital.dto.response.*;
import com.ssafy.aitime.domain.hospital.entity.Hospital;
import com.ssafy.aitime.domain.hospital.entity.HospitalChildren;
import com.ssafy.aitime.domain.hospital.entity.HospitalStaff;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.StaffRole;
import com.ssafy.aitime.domain.hospital.exception.DoctorNotFoundException;
import com.ssafy.aitime.domain.hospital.exception.HospitalStaffAccessDeniedException;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import com.ssafy.aitime.domain.hospital.repository.HospitalStaffRepository;
import com.ssafy.aitime.domain.hospital.repository.ReservationRepository;
import com.ssafy.aitime.domain.user.entity.User;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

import java.lang.reflect.Method;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
// ✅ 헬퍼 메서드에서 공통으로 설정한 Stubbing 중 일부가 호출되지 않아도 에러를 무시하도록 설정
@MockitoSettings(strictness = Strictness.LENIENT)
class DoctorServiceImplTest {

    @Mock private ReservationRepository reservationRepository;
    @Mock private HospitalChildrenRepository hospitalChildrenRepository;
    @Mock private HospitalStaffRepository hospitalStaffRepository;
    @Mock private ChildRepository childRepository;
    @Mock private ExamService examService;
    @Mock private VideoService videoService;

    @InjectMocks
    private DoctorServiceImpl doctorService;

    @Nested
    @DisplayName("환자 목록 검색 테스트")
    class SearchPatientTest {

        @Test
        @DisplayName("날짜 필터와 페이징이 적용된 환자 목록을 반환한다")
        void getSearchPatientList_success() {
            // given
            UUID doctorId = UUID.randomUUID();
            PatientSearchRequest req = mock(PatientSearchRequest.class);
            LocalDate filterDate = LocalDate.of(2026, 1, 26);

            given(req.getEffectiveDate()).willReturn(filterDate);
            given(req.hasNameFilter()).willReturn(false);
            given(req.hasResultStatusFilter()).willReturn(false);
            given(req.page()).willReturn(0);
            given(req.size()).willReturn(10);

            given(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(any(), any(), any())).willReturn(true);

            UUID hcId = UUID.randomUUID();
            Reservation res = mock(Reservation.class);
            HospitalChildren hc = mockHospitalChildren(hcId, UUID.randomUUID(), UUID.randomUUID());
            given(res.getHospitalChildren()).willReturn(hc);
            given(reservationRepository.findByDoctorIdAndReservationStatusNotAndScheduledAtBetween(any(), any(), any(), any()))
                    .willReturn(List.of(res));

            Child child = mockChild(UUID.randomUUID(), "홍길동");
            given(hc.getChild()).willReturn(child);
            given(hospitalChildrenRepository.findByHospitalChildrenIdInAndLinkStatus(anyList(), any())).willReturn(List.of(hc));
            given(childRepository.findByChildIdInAndRecordStatus(anyList(), any())).willReturn(List.of(child));
            given(examService.getExamsByChildIds(anyList())).willReturn(Collections.emptyList());

            // when
            PatientSearchResponse resp = doctorService.getSearchPatientList(doctorId, req);

            // then
            assertThat(extractTotal(resp)).isEqualTo(1);
            assertThat(extractList(resp)).hasSize(1);
        }

        @Test
        @DisplayName("의사가 존재하지 않으면 DoctorNotFoundException이 발생한다")
        void getSearchPatientList_doctorNotFound() {
            given(hospitalStaffRepository.existsByHospitalStaffIdAndStaffRoleAndRecordStatus(any(), any(), any())).willReturn(false);
            assertThatThrownBy(() -> doctorService.getSearchPatientList(UUID.randomUUID(), mock(PatientSearchRequest.class)))
                    .isInstanceOf(DoctorNotFoundException.class);
        }
    }

    @Nested
    @DisplayName("상세 정보 및 레포트 조회 테스트")
    class DetailInfoTest {

        @Test
        @DisplayName("특정 환아의 검사 목록과 비디오 요약을 조회한다")
        void getExamsByHospitalChildren_success() {
            // given
            UUID staffId = UUID.randomUUID();
            UUID hcId = UUID.randomUUID();
            UUID hospitalId = UUID.randomUUID();
            UUID childId = UUID.randomUUID();

            HospitalStaff staff = mockStaff(staffId, hospitalId);
            HospitalChildren hc = mockHospitalChildren(hcId, hospitalId, childId);

            given(hospitalStaffRepository.findById(staffId)).willReturn(Optional.of(staff));
            given(hospitalChildrenRepository.findById(hcId)).willReturn(Optional.of(hc));

            Exam exam = mock(Exam.class);
            UUID examId = UUID.randomUUID();
            given(exam.getExamId()).willReturn(examId);
            given(exam.getExamStatus()).willReturn(ExamStatus.COMPLETED);
            given(exam.getCreatedAt()).willReturn(LocalDateTime.now());
            given(examService.getExamsByChildId(childId)).willReturn(List.of(exam));

            Video video = mock(Video.class);
            given(video.getExam()).willReturn(exam);
            given(video.getVideoId()).willReturn(UUID.randomUUID());
            given(video.getVideoType()).willReturn(VideoType.POSE_IMITATION);
            given(videoService.getVideosByExamIds(anyList())).willReturn(List.of(video));

            // when
            List<ExamWithVideosResponse> result = doctorService.getExamsByHospitalChildren(staffId, hcId);

            // then
            assertThat(result).hasSize(1);
            assertThat(result.get(0).videos()).hasSize(1);
        }

        @Test
        @DisplayName("다른 병원 소속의 검사 상세 정보를 조회하면 예외가 발생한다")
        void getAdosDetail_accessDenied() {
            // given
            UUID staffId = UUID.randomUUID();
            UUID examId = UUID.randomUUID();
            HospitalStaff staff = mockStaff(staffId, UUID.randomUUID()); // 병원 A

            Exam exam = mock(Exam.class);
            given(exam.getChild()).willReturn(mock(Child.class));
            given(hospitalStaffRepository.findById(staffId)).willReturn(Optional.of(staff));
            given(examService.getExamById(examId)).willReturn(exam);

            // 병원 B와 연동된 상태 (false)
            given(hospitalChildrenRepository.existsByChildAndHospitalAndLinkStatus(any(), any(), any())).willReturn(false);

            // when & then
            assertThatThrownBy(() -> doctorService.getAdosDetail(staffId, examId))
                    .isInstanceOf(HospitalStaffAccessDeniedException.class);
        }

        @Test
        @DisplayName("초기 레포트 데이터를 통합하여 반환한다")
        void getInitialReport_success() {
            // given
            UUID staffId = UUID.randomUUID();
            UUID hcId = UUID.randomUUID();
            UUID hospitalId = UUID.randomUUID();
            UUID childId = UUID.randomUUID();
            UUID examId = UUID.randomUUID();

            HospitalStaff staff = mockStaff(staffId, hospitalId);
            HospitalChildren hc = mockHospitalChildren(hcId, hospitalId, childId);

            given(hospitalStaffRepository.findById(staffId)).willReturn(Optional.of(staff));
            given(hospitalChildrenRepository.findById(hcId)).willReturn(Optional.of(hc));

            Exam exam = mock(Exam.class);
            given(exam.getExamId()).willReturn(examId);
            given(exam.getExamStatus()).willReturn(ExamStatus.COMPLETED);
            given(exam.getCreatedAt()).willReturn(LocalDateTime.now());
            given(examService.getExamsByChildId(childId)).willReturn(List.of(exam));
            given(videoService.getVideosByExamIds(anyList())).willReturn(Collections.emptyList());

            given(examService.getAdosGraphData(childId)).willReturn(mock(AdosReportGraphsResponse.class));
            given(examService.getAdosDetail(examId)).willReturn(mock(AdosDetailResponse.class));

            // when
            InitialReportResponse response = doctorService.getInitialReport(staffId, hcId, 300L);

            // then
            assertThat(response).isNotNull();
            assertThat(response.examVideoList()).isNotEmpty();
        }
    }

    // ---------------- Helper Methods ----------------

    private HospitalStaff mockStaff(UUID staffId, UUID hospitalId) {
        HospitalStaff staff = mock(HospitalStaff.class);
        Hospital hospital = mock(Hospital.class);
        given(hospital.getHospitalId()).willReturn(hospitalId);
        given(staff.getHospital()).willReturn(hospital);
        given(staff.getHospitalStaffId()).willReturn(staffId);
        return staff;
    }

    private HospitalChildren mockHospitalChildren(UUID hcId, UUID hospitalId, UUID childId) {
        HospitalChildren hc = mock(HospitalChildren.class);
        Hospital hospital = mock(Hospital.class);
        Child child = mock(Child.class);

        given(hospital.getHospitalId()).willReturn(hospitalId);
        given(child.getChildId()).willReturn(childId);
        given(hc.getHospital()).willReturn(hospital);
        given(hc.getChild()).willReturn(child);
        given(hc.getHospitalChildrenId()).willReturn(hcId);
        given(hc.getLinkStatus()).willReturn(LinkStatus.ACTIVE);
        return hc;
    }

    private Child mockChild(UUID childId, String name) {
        Child child = mock(Child.class);
        User user = mock(User.class);
        given(user.getUserId()).willReturn(UUID.randomUUID());
        given(child.getChildId()).willReturn(childId);
        given(child.getUser()).willReturn(user);
        given(child.getName()).willReturn(name);
        given(child.getBirthdate()).willReturn(LocalDate.of(2020, 1, 1));
        given(child.getGender()).willReturn(Gender.MALE);
        return child;
    }

    // ---------------- Reflection Helpers (DTO 검증용) ----------------

    @SuppressWarnings("unchecked")
    private static List<?> extractList(Object resp) {
        for (String m : List.of("childResponses", "getChildResponses", "items", "getItems")) {
            Object v = tryInvoke(resp, m);
            if (v instanceof List) return (List<?>) v;
        }
        return Collections.emptyList();
    }

    private static int extractTotal(Object resp) {
        for (String m : List.of("totalCount", "getTotalCount", "total", "getTotal")) {
            Object v = tryInvoke(resp, m);
            if (v instanceof Integer i) return i;
            if (v instanceof Long l) return l.intValue();
        }
        return 0;
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