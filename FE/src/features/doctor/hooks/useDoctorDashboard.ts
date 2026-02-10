import { useState, useEffect, useCallback } from "react";
import { doctorApi } from "../api/doctorApi";
import { examReportApi } from "../api/examReportApi";
import type { PatientDetailFull, PatientDto } from "../types/doctor";
import type {
  ExamReportInitialData,
  ExamVideoListItem,
  VideoPresignView,
  AdosGraphs,
  AdosDetail,
  AdosUpdateRequest,
} from "@/api/types/examReport.types";
import { MASTER_ADOS_ITEMS, CODES_PRE_VERBAL, CODES_VERBAL } from "../types/ados";

export const useDoctorDashboard = () => {
  // --- UI 상태 ---
  const [isVideoModalOpen, setVideoModalOpen] = useState(false);
  const [isAdosModalOpen, setAdosModalOpen] = useState(false);

  // --- 환자 및 대기열 상태 ---
  const [waitingList, setWaitingList] = useState<PatientDto[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientDetailFull | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // --- API 데이터 상태 ---
  const [examReportData, setExamReportData] = useState<ExamReportInitialData | null>(null);
  const [examVideoList, setExamVideoList] = useState<ExamVideoListItem[]>([]);
  const [currentVideoData, setCurrentVideoData] = useState<VideoPresignView | null>(null);
  const [adosGraphs, setAdosGraphs] = useState<AdosGraphs | null>(null);
  const [currentAdosDetail, setCurrentAdosDetail] = useState<AdosDetail | null>(null);

  const [isExamReportLoading, setIsExamReportLoading] = useState(false);

  /**
   * [스마트 데이터 로딩]
   * 1순위: 통합 API (/initial) 시도 -> 성공 시 한 번에 렌더링
   * 2순위: 실패 시(500 등) -> 개별 API로 나머지 데이터(목록, 그래프, 점수) 복구 시도
   */
  const loadExamReportInitialData = useCallback(async (hospitalChildrenId: string) => {
    setIsExamReportLoading(true);

    // 1. 통합 API 시도
    try {
      console.log(`📡 [Dashboard] 통합 데이터 요청: ${hospitalChildrenId}`);
      const data = await examReportApi.getExamReportsInitial(hospitalChildrenId);

      // 성공 시 데이터 설정
      setExamReportData(data);
      setExamVideoList(data.examVideoList || []);
      setAdosGraphs(data.adosGraphs);
      setCurrentAdosDetail(data.latestAdosDetail);
      setCurrentVideoData(data.latestPoseImitationVideo || null);

      console.log("✅ [Dashboard] 통합 데이터 로딩 완료");
      return; // 여기서 종료
    } catch (error: any) {
      console.warn("⚠️ [Dashboard] 통합 API 실패 (S3 에러 등). 개별 API로 복구 시도합니다.", error);
    }

    // 2. 통합 API 실패 시 -> 개별 API로 복구 (Fallback)
    try {
      // (1) 검사 목록 조회
      console.log("📡 [Recovery] 검사 목록 별도 조회...");
      const exams = await examReportApi.getExamList(hospitalChildrenId);
      setExamVideoList(exams || []);

      // (2) ADOS 그래프 조회
      console.log("📡 [Recovery] 그래프 데이터 별도 조회...");
      const graphs = await examReportApi.getAdosGraphs(hospitalChildrenId);
      setAdosGraphs(graphs);

      // (3) 최신 ADOS 상세 조회 (검사 목록이 있을 경우 최신 건 조회)
      if (exams && exams.length > 0) {
        const latestExamId = exams[0].examId;
        console.log(`📡 [Recovery] 최신 ADOS 상세 조회 (${latestExamId})...`);
        const adosDetail = await examReportApi.getAdosDetail(latestExamId);
        setCurrentAdosDetail(adosDetail);
      } else {
        setCurrentAdosDetail(null);
      }

      // (4) 비디오는 에러가 난 것이므로 null 처리
      setCurrentVideoData(null);

      console.log("✅ [Recovery] 부분 데이터 복구 완료 (비디오 제외)");
    } catch (fallbackError) {
      // 개별 조회마저 실패했을 때
      console.error("❌ [Dashboard] 데이터 복구 실패:", fallbackError);

      setExamReportData(null);
      setExamVideoList([]);
      setAdosGraphs(null);
      setCurrentAdosDetail(null);
      setCurrentVideoData(null);
    } finally {
      setIsExamReportLoading(false);
    }
  }, []);

  /**
   * [API 3] 비디오 선택
   */
  const selectVideo = useCallback(async (examId: string, videoId: string) => {
    try {
      console.log(`📡 [Video] 상세 조회 요청: ${videoId}`);
      const videoData = await examReportApi.getVideoPresignViewWithTimestamps(examId, videoId);
      setCurrentVideoData(videoData);
    } catch (error) {
      console.error("❌ [Video] 로딩 실패:", error);
      alert("영상을 불러올 수 없습니다. (서버 파일 누락 가능성)");
    }
  }, []);

  /**
   * [API 5] ADOS 상세 조회 (과거 이력 클릭 시)
   */
  const loadAdosDetail = useCallback(async (examId: string) => {
    try {
      const detail = await examReportApi.getAdosDetail(examId);
      setCurrentAdosDetail(detail);
    } catch (error) {
      console.error("❌ [ADOS] 상세 조회 실패:", error);
    }
  }, []);

  /**
   * [API 6] ADOS 수정 (비활성화)
   */
  /**
   * [API 6] ADOS 수정 (로컬 상태 업데이트)
   * API 미구현 시점까지 로컬 상태만 변경하여 "저장된 것처럼" 처리
   */
  const updateAdos = useCallback(async (_examId: string, scores: AdosUpdateRequest) => {
    // 1. 현재 상태 복제
    if (!currentAdosDetail) {
      console.warn("⚠️ 업데이트할 상세 정보가 없습니다.");
      return;
    }

    // 2. 새로운 점수 반영 (기존 점수 + 새 점수 병합)
    const updatedScores = { ...currentAdosDetail.scores };
    Object.entries(scores).forEach(([key, value]) => {
      // API Key (a2) 형식을 그대로 사용
      updatedScores[key] = value;
    });

    // 3. 총점 재계산 로직
    // [중요] 환자 연령에 따라 Verbal/Pre-Verbal 필터링
    const patientMonth = selectedPatient?.monthlyAge || 0;
    const isVerbal = patientMonth > 21; // 21개월 초과 시 Verbal 간주 (AdosModal 기준)





    const targetCodes = patientMonth >= 12 && patientMonth <= 21
      ? CODES_PRE_VERBAL
      : (isVerbal ? CODES_VERBAL : CODES_PRE_VERBAL);

    let newSaTotal = 0;
    let newRrbTotal = 0;

    targetCodes.forEach(code => {
      // 마스터 아이템 찾기
      const item = MASTER_ADOS_ITEMS.find(i => i.code === code);
      if (!item) return;

      // 점수 찾기 (API 키 포맷인 소문자 key를 찾아야 함)
      // code (A-2) -> key (a2)
      const apiKey = code.replace("-", "").toLowerCase();
      const scoreVal = updatedScores[apiKey];

      if (typeof scoreVal === 'number') {
        if (item.category === 'SA') newSaTotal += scoreVal;
        if (item.category === 'RRB') newRrbTotal += scoreVal;
      }
    });

    updatedScores.socialAffectTotal = newSaTotal;
    updatedScores.rrbTotal = newRrbTotal;
    updatedScores.total = newSaTotal + newRrbTotal;

    console.log("📝 [ADOS Update] Local State Updated:", updatedScores);

    // 4. 상태 업데이트
    setCurrentAdosDetail({
      ...currentAdosDetail,
      scores: updatedScores
    });

    // alert("저장되었습니다 (로컬 반영)"); // 사용자 경험상 알림 제거 또는 Toast 권장
  }, [currentAdosDetail, selectedPatient]);

  /**
   * 환자 선택 핸들러
   */
  const selectPatient = useCallback((patient: PatientDto) => {
    const patientDetail = doctorApi.getPatientDetailFromDto(patient);
    setSelectedPatient(patientDetail);

    const targetId = patient.hospitalChildrenId || patient.childId;
    console.log(`📋 환자 선택됨: ${patient.childName} (ID: ${targetId})`);

    if (targetId) {
      loadExamReportInitialData(targetId);
    } else {
      console.warn("⚠️ 유효하지 않은 ID입니다.");
    }
  }, [loadExamReportInitialData]);

  /**
   * 초기 대기열 로딩
   */
  useEffect(() => {
    const fetchWaitingList = async () => {
      setIsLoading(true);
      try {
        const today = new Date();
        const dateStr = today.toISOString().split('T')[0];

        const response = await doctorApi.searchPatients({
          page: 0,
          size: 100,
          date: dateStr,
          year: today.getFullYear(),
          month: today.getMonth() + 1,
          day: today.getDate(),
          effectiveDate: dateStr
        });

        if (response.code === 200 && response.data?.data?.length > 0) {
          const patients = response.data.data;
          setWaitingList(patients);
          selectPatient(patients[0]);
        } else {
          setWaitingList([]);
          setSelectedPatient(null);
        }
      } catch (error) {
        console.error("API Error:", error);
        setWaitingList([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetchWaitingList();
  }, [selectPatient]);

  return {
    states: {
      isVideoModalOpen,
      isAdosModalOpen,
      selectedPatient,
      waitingList,
      isLoading,
      examReportData,
      examVideoList,
      currentVideoData,
      adosGraphs,
      currentAdosDetail,
      isExamReportLoading,
    },
    actions: {
      setVideoModalOpen,
      setAdosModalOpen,
      selectPatient,
      selectVideo,
      loadAdosDetail,
      updateAdos,
    },
  };
};