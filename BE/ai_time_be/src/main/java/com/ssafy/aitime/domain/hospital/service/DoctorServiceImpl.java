package com.ssafy.aitime.domain.hospital.service;

import com.ssafy.aitime.common.enums.RecordStatus;
import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.child.repository.ChildRepository;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.hospital.dto.response.ChildResponse;
import com.ssafy.aitime.domain.hospital.dto.response.TotalPatientListResponse;
import com.ssafy.aitime.domain.hospital.entity.Reservation;
import com.ssafy.aitime.domain.hospital.entity.enums.LinkStatus;
import com.ssafy.aitime.domain.hospital.entity.enums.ReservationStatus;
import com.ssafy.aitime.domain.hospital.repository.HospitalChildrenRepository;
import com.ssafy.aitime.domain.hospital.repository.ReservationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
@RequiredArgsConstructor
public class DoctorServiceImpl implements DoctorService{

    private final ReservationRepository reservationRepository;
    private final HospitalChildrenRepository hospitalChildrenRepository;
    private final ChildRepository childRepository;
    private final ExamRepository examRepository;

    private int calcMonthlyAge(LocalDate birthdate) {
        return (int) ChronoUnit.MONTHS.between(birthdate, LocalDate.now());
    }

    @Override
    public TotalPatientListResponse getTotalPatientList(UUID doctorId) {
        // TODO 1: doctorId로 reservation 테이블에서 환자-병원 UUID 뽑기
        List<UUID> hospitalChildrenIds =
                reservationRepository.findByDoctorIdAndReservationStatusNot(
                        doctorId,
                        ReservationStatus.CANCELLED
                )
                .stream()
                .map(r -> r.getHospitalChildren().getHospitalChildrenId())
                .distinct()
                .toList();

        // TODO 2: hospitalChildrenIds를 이용하여 hospital_children 테이블에서 child_id UUID 뽑기
        List<UUID> childIds = hospitalChildrenRepository
                .findByHospitalChildrenIdInAndLinkStatus(hospitalChildrenIds, LinkStatus.ACTIVE)
                .stream()
                .map(hc -> hc.getChild().getChildId())
                .distinct()
                .toList();

        // TODO 3: childIds를 이용하여 child 테이블에서 객체 받아오기
        List<Child> childs = childRepository.findByChildIdInAndRecordStatus(childIds, RecordStatus.ACTIVE);

        // TODO 4: childIds로 exam 다 가져오기
        List<Exam> exams = examRepository.findByChild_ChildIdInOrderByCompletedAtDesc(childIds);

        // TODO 5: childId와 exam result
        Map<UUID, String> latestExamStatusByChildId = new HashMap<>();

        for (Exam e : exams) {
            UUID childId = e.getChild().getChildId();

            // 이미 있으면 스킵 (createdAt desc라서 처음이 최신)
            latestExamStatusByChildId.putIfAbsent(childId, e.getExamStatus().name());
        }

        // TODO 5: DTO로 변환해서 반환
        List<ChildResponse> responses = new ArrayList<>();

        for (Child child : childs) {
            UUID childId = child.getChildId();

            String latestExamStatus = latestExamStatusByChildId.getOrDefault(childId, "NONE");

            int monthlyAge = calcMonthlyAge(child.getBirthdate());

            responses.add(new ChildResponse(
                    childId,
                    child.getUser().getUserId(),
                    child.getName(),
                    monthlyAge,
                    child.getBirthdate(),
                    child.getGender().name(),
                    latestExamStatus
            ));
        }

        return new TotalPatientListResponse(responses, responses.size());
    }
}
