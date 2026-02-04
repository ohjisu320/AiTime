package com.ssafy.aitime.domain.exam.service;


import com.ssafy.aitime.domain.child.entity.Child;
import com.ssafy.aitime.domain.exam.entity.Ados;
import com.ssafy.aitime.domain.exam.entity.Exam;
import com.ssafy.aitime.domain.exam.entity.Video;
import com.ssafy.aitime.domain.exam.entity.assessment.NameFacingTrial;
import com.ssafy.aitime.domain.exam.entity.assessment.NameNonFacingTrial;
import com.ssafy.aitime.domain.exam.entity.assessment.PoseImitationTrial;
import com.ssafy.aitime.domain.exam.entity.assessment.SpeechImitationTrial;
import com.ssafy.aitime.domain.exam.entity.enums.AnalysisStatus;
import com.ssafy.aitime.domain.exam.entity.enums.VideoType;
import com.ssafy.aitime.domain.exam.repository.AdosRepository;
import com.ssafy.aitime.domain.exam.repository.ExamRepository;
import com.ssafy.aitime.domain.exam.repository.VideoRepository;
import com.ssafy.aitime.domain.exam.repository.assessment.NameFacingTrialRepository;
import com.ssafy.aitime.domain.exam.repository.assessment.NameNonFacingTrialRepository;
import com.ssafy.aitime.domain.exam.repository.assessment.PoseImitationTrialRepository;
import com.ssafy.aitime.domain.exam.repository.assessment.SpeechImitationTrialRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.Period;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AdosCalculationServiceImpl implements AdosCalculationService{

    private final ExamRepository examRepository;
    private final VideoRepository videoRepository;
    private final AdosRepository adosRepository;

    private final PoseImitationTrialRepository poseTrialRepository;
    private final SpeechImitationTrialRepository speechTrialRepository;
    private final NameFacingTrialRepository nameFacingTrialRepository;
    private final NameNonFacingTrialRepository nameNonFacingTrialRepository;

    /**
     * 4개 영상 분석 완료 확인 후 ADOS 계산
     */
    @Override
    @Transactional
    public void calculateAndSaveAdos(UUID examId) {
        log.info("=== ADOS 계산 시작 - examId: {}", examId);

        // 1. 4개 영상 모두 분석 완료되었는지 확인
        if (!isAllVideosAnalyzed(examId)) {
            log.warn("⚠️ 4개 영상이 모두 분석 완료되지 않음 - examId: {}", examId);
            return;
        }

        // 2. Exam 조회
        Exam exam = examRepository.findById(examId)
                .orElseThrow(() -> new IllegalArgumentException("Exam not found: " + examId));

        // 3. 각 Trial 조회
        List<Video> videos = videoRepository.findByExamExamId(examId);

        Video poseVideo = findVideoByType(videos, VideoType.POSE_IMITATION);
        Video speechVideo = findVideoByType(videos, VideoType.SPEECH_IMITATION);
        Video nameFacingVideo = findVideoByType(videos, VideoType.NAME_FACING);
        Video nameNonFacingVideo = findVideoByType(videos, VideoType.NAME_NON_FACING);

        PoseImitationTrial poseTask = poseTrialRepository.findByVideo(poseVideo)
                .orElseThrow(() -> new IllegalStateException("PoseImitationTrial not found for videoId: " + poseVideo.getVideoId()));

        SpeechImitationTrial speechTask = speechTrialRepository.findByVideo(speechVideo)
                .orElseThrow(() -> new IllegalStateException("SpeechImitationTrial not found for videoId: " + speechVideo.getVideoId()));

        NameFacingTrial nameFacingTask = nameFacingTrialRepository.findByVideo(nameFacingVideo)
                .orElseThrow(() -> new IllegalStateException("NameFacingTrial not found for videoId: " + nameFacingVideo.getVideoId()));

        NameNonFacingTrial nameNonFacingTask = nameNonFacingTrialRepository.findByVideo(nameNonFacingVideo)
                .orElseThrow(() -> new IllegalStateException("NameNonFacingTrial not found for videoId: " + nameNonFacingVideo.getVideoId()));

        // 4. 아이 개월수 계산
        Long ageMonths = calculateAgeMonths(exam.getChild());
        AdosAgeGroup ageGroup = determineAgeGroup(ageMonths);

        log.info("아이 개월수: {}개월, 그룹: {}", ageMonths, ageGroup);

        // 5. ADOS 점수 계산
        AdosScores scores = calculateAdosScores(poseTask, speechTask, nameFacingTask, nameNonFacingTask, ageGroup);

        // 6. ADOS 엔티티 생성 및 저장
        Ados ados = Ados.builder()
                .exam(exam)
                // A 섹션
                .a2(scores.a2)
                .a3(scores.a3)
                .a7(scores.a7)
                .a8(scores.a8)
                // B 섹션
                .b1(scores.b1)
                .b4(scores.b4)
                .b5(scores.b5)
                .b6(scores.b6)
                .b7(scores.b7)
                .b8(scores.b8)
                .b9(scores.b9)
                .b12(scores.b12)
                .b13(scores.b13)
                .b14(scores.b14)
                .b15(scores.b15)
                .b16b(scores.b16b)
                .b18(scores.b18)
                .socialAffectTotal(scores.socialAffectTotal)
                // D 섹션
                .d1(scores.d1)
                .d2(scores.d2)
                .d5(scores.d5)
                .rrbTotal(scores.rrbTotal)
                // 전체 총점
                .total(scores.total)
                .build();

        adosRepository.save(ados);

        log.info("✅ ADOS 저장 완료 - examId: {}, total: {}, socialAffect: {}, rrb: {}",
                examId, scores.total, scores.socialAffectTotal, scores.rrbTotal);
    }

    /**
     * 4개 영상이 모두 분석 완료되었는지 확인
     */
    private boolean isAllVideosAnalyzed(UUID examId) {
        long successCount = videoRepository.countByExamIdAndAnalysisStatus(
                examId,
                AnalysisStatus.SUCCESS
        );
        return successCount == 4;
    }

    /**
     * VideoType으로 Video 찾기
     */
    private Video findVideoByType(List<Video> videos, VideoType videoType) {
        return videos.stream()
                .filter(v -> v.getVideoType() == videoType)
                .findFirst()
                .orElseThrow(() -> new IllegalStateException("Video not found for type: " + videoType));
    }

    /**
     * 아이 개월수 계산
     */
    private Long calculateAgeMonths(Child child) {
        LocalDate birthDate = child.getBirthdate();
        if (birthDate == null) {
            log.warn("⚠️ Child의 birthDate가 null입니다.");
            return 0L;
        }

        LocalDate now = LocalDate.now();
        Period period = Period.between(birthDate, now);

        long totalMonths = period.getYears() * 12L + period.getMonths();

        log.debug("아이 개월수 계산 - birthDate: {}, 현재: {}, 개월수: {}", birthDate, now, totalMonths);

        return totalMonths;
    }

    /**
     * 연령 그룹 결정
     *
     * 현재는 개월수만으로 판단
     * 추후 "말하는" 여부를 판단하는 로직 추가 필요
     */
    private AdosAgeGroup determineAgeGroup(Long ageMonths) {
        if (ageMonths == null || ageMonths < 12) {
            throw new IllegalArgumentException("12개월 미만은 ADOS 검사 대상이 아닙니다.");
        }

        if (ageMonths <= 20) {
            // 12-20개월은 무조건 GROUP_A
            return AdosAgeGroup.GROUP_A;
        }

        if (ageMonths <= 30) {
            // 21-30개월은 말하는지 여부로 구분
            // TODO: 말하는지 여부를 판단하는 로직 추가 필요
            // 현재는 일단 GROUP_A로 설정 (보수적 접근)
            return AdosAgeGroup.GROUP_A;
        }

        // 31개월 이상
        throw new IllegalArgumentException("30개월 초과는 ADOS-2 Toddler Module 대상이 아닙니다.");
    }

    /**
     * ADOS 점수 계산
     */
    private AdosScores calculateAdosScores(
            PoseImitationTrial poseTask,
            SpeechImitationTrial speechTask,
            NameFacingTrial nameFacingTask,
            NameNonFacingTrial nameNonFacingTask,
            AdosAgeGroup ageGroup) {

        AdosScores scores = new AdosScores();

        // ========== AI가 제공하는 데이터 ==========

        // Task1 (POSE_IMITATION): A8, B6, B18
        scores.a8 = parseInteger(poseTask.getAdosA8());
        // B6는 특별 계산 필요 (아래에서)

        // Task2 (SPEECH_IMITATION): A3, B18
        scores.a3 = parseInteger(speechTask.getAdosA3());

        // Task3 (NAME_FACING): B1, B4, B6, B18
        scores.b1 = parseInteger(nameFacingTask.getAdosB1());
        scores.b4 = parseInteger(nameFacingTask.getAdosB4());

        // Task4 (NAME_NON_FACING): B7, B18
        scores.b7 = parseInteger(nameNonFacingTask.getAdosB7());

        // ========== 특수 계산 필요한 항목 ==========

        // B6: 동작모방(task1) + 대면호명(task3)의 T/F 조합
        scores.b6 = calculateB6Score(
                poseTask.getAdosB6(),
                nameFacingTask.getAdosB6()
        );

        // B18: 4개 Task 모두의 T/F 합산
        scores.b18 = calculateB18Score(
                poseTask.getAdosB18(),
                speechTask.getAdosB18(),
                nameFacingTask.getAdosB18(),
                nameNonFacingTask.getAdosB18()
        );

        // ========== AI가 제공하지 않는 항목들 (null 또는 0) ==========

        scores.a2 = null;   // 다른 사람을 향해 목소리를 내는 빈도
        scores.a7 = null;   // 가리키기
        scores.b5 = null;   // 도입 행동 동안의 응시와 통합
        scores.b8 = null;   // 무시하기
        scores.b9 = null;   // 요청하기
        scores.b12 = null;  // 보여주기
        scores.b13 = null;  // 합동 주시를 자발적으로 시도하기
        scores.b14 = null;  // 합동 주시에 대한 반응
        scores.b15 = null;  // 도입 행동의 질
        scores.b16b = null; // 도입 행동의 양 - 부모/양육자
        scores.d1 = null;   // 놀잇감/사람에 대한 특이한 감각적 흥미
        scores.d2 = null;   // 손과 손가락 움직임/자세
        scores.d5 = null;   // 특이하게 반복적인 흥미

        // ========== Total 계산 ==========

        scores.calculateTotals(ageGroup);

        return scores;
    }

    /**
     * B6 점수 계산
     *
     * 동작모방(task1) + 대면호명(task3)의 T/F 조합
     * TT → 0, TF/FT → 1, FF → 3
     */
    private Integer calculateB6Score(String poseB6, String nameFacingB6) {
        boolean pose = parseBoolean(poseB6);
        boolean facing = parseBoolean(nameFacingB6);

        if (pose && facing) {
            return 0;  // TT
        } else if (pose || facing) {
            return 1;  // TF or FT
        } else {
            return 3;  // FF
        }
    }

    /**
     * B18 점수 계산
     *
     * 4개 Task 모두의 T/F 합산
     * T 4개 → 0, T 3개 → 1, T 2개 → 2, T 1/0개 → 3
     */
    private Integer calculateB18Score(String... b18Values) {
        long trueCount = 0;

        for (String value : b18Values) {
            if (parseBoolean(value)) {
                trueCount++;
            }
        }

        return switch ((int) trueCount) {
            case 4 -> 0;
            case 3 -> 1;
            case 2 -> 2;
            default -> 3;  // 1 or 0
        };
    }

    /**
     * String → Boolean 변환
     */
    private boolean parseBoolean(String value) {
        if (value == null) return false;
        return "TRUE".equalsIgnoreCase(value.trim());
    }

    /**
     * String → Integer 변환
     */
    private Integer parseInteger(String value) {
        if (value == null || value.trim().isEmpty()) return null;
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            log.warn("⚠️ Integer 파싱 실패: {}", value);
            return null;
        }
    }

    /**
     * 연령 그룹 Enum
     */
    public enum AdosAgeGroup {
        GROUP_A,  // 12-20개월 또는 말 못하는 21-30개월
        GROUP_B   // 말하는 21-30개월
    }

    /**
     * ADOS 점수 모음 클래스
     */
    private static class AdosScores {
        // A 섹션
        Integer a2, a3, a7, a8;

        // B 섹션
        Integer b1, b4, b5, b6, b7, b8, b9, b12, b13, b14, b15, b16b, b18;

        // D 섹션
        Integer d1, d2, d5;

        // Totals
        Integer socialAffectTotal;
        Integer rrbTotal;
        Integer total;

        /**
         * Total 계산
         *
         * 개월수에 따라 다른 필드를 합산
         */
        void calculateTotals(AdosAgeGroup ageGroup) {
            if (ageGroup == AdosAgeGroup.GROUP_A) {
                // 12-20개월 또는 말 못하는 21-30개월
                socialAffectTotal = sumNonNull(a2, a8, b1, b4, b5, b6, b12, b13, b14, b15);
                rrbTotal = sumNonNull(a3, d1, d2, d5);
            } else {
                // 말하는 21-30개월
                socialAffectTotal = sumNonNull(a7, b1, b4, b5, b6, b7, b8, b9, b13, b15, b16b, b18);
                rrbTotal = sumNonNull(a3, d1, d2, d5);
            }

            total = (socialAffectTotal != null ? socialAffectTotal : 0) +
                    (rrbTotal != null ? rrbTotal : 0);
        }

        /**
         * null이 아닌 값들만 합산
         */
        private Integer sumNonNull(Integer... values) {
            int sum = 0;
            boolean hasValue = false;

            for (Integer value : values) {
                if (value != null) {
                    sum += value;
                    hasValue = true;
                }
            }

            return hasValue ? sum : null;
        }
    }
}
