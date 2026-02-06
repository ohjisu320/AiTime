// src/features/doctor/hooks/useDoctorDashboard.ts
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

export const useDoctorDashboard = () => {
  // --- UI 상태 ---
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [isVideoModalOpen, setVideoModalOpen] = useState(false);
  const [isAdosModalOpen, setAdosModalOpen] = useState(false);

  // --- 환자 및 대기열 상태 ---
  const [waitingList, setWaitingList] = useState<PatientDto[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientDetailFull | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // --- API 데이터 상태 (Mock 제거됨) ---
  const [examReportData, setExamReportData] = useState<ExamReportInitialData | null>(null);
  const [examVideoList, setExamVideoList] = useState<ExamVideoListItem[]>([]);
  const [currentVideoData, setCurrentVideoData] = useState<VideoPresignView | null>(null);
  const [adosGraphs, setAdosGraphs] = useState<AdosGraphs | null>(null);
  const [currentAdosDetail, setCurrentAdosDetail] = useState<AdosDetail | null>(null);

  const [isExamReportLoading, setIsExamReportLoading] = useState(false);

  /**
   * [API 0] 통합 초기 데이터 로딩
   * GET /api/v1/doctor/{hospitalChildrenId}/exam-reports/initial
   * 
   * 환자 선택 시 한 번 호출되어 화면의 모든 섹션을 채웁니다.
   */
  const loadExamReportInitialData = useCallback(async (hospitalChildrenId: string) => {
    setIsExamReportLoading(true);
    try {
      console.log(`📡 [Dashboard] 초기 데이터 요청: ${hospitalChildrenId}`);

      // 통합 API 호출
      const data = await examReportApi.getExamReportsInitial(hospitalChildrenId);

      // 전체 데이터 저장
      setExamReportData(data);

      // 1. 세션 목록 업데이트
      setExamVideoList(data.examVideoList || []);

      // 2. 그래프 업데이트
      setAdosGraphs(data.adosGraphs);

      // 3. ADOS 상세 업데이트 (초기값: 최신 검사 기준)
      setCurrentAdosDetail(data.latestAdosDetail);

      // 4. 비디오 업데이트 (최신 POSE_IMITATION이 있는 경우만)
      if (data.latestPoseImitationVideo) {
        setCurrentVideoData(data.latestPoseImitationVideo);
      } else {
        setCurrentVideoData(null);
      }

      console.log("✅ [Dashboard] 데이터 로딩 완료");
    } catch (error) {
      console.error("❌ [Dashboard] 데이터 로딩 실패:", error);
      // 에러 시 상태 초기화
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
   * [API 3] 비디오 선택 (presign-view)
   * 세션 목록에서 비디오 클릭 시 호출
   */
  const selectVideo = useCallback(async (videoId: string) => {
    try {
      console.log(`📡 [Video] 상세 조회 요청: ${videoId}`);
      const videoData = await examReportApi.getVideoPresignView(videoId);
      setCurrentVideoData(videoData);
    } catch (error) {
      console.error("❌ [Video] 로딩 실패:", error);
    }
  }, []);

  /**
   * [API 5] ADOS 상세 조회
   * 특정 과거 검사의 ADOS 점수를 보고 싶을 때 호출
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
   * [API 6] ADOS 수정
   * 수정 후 그래프 데이터도 갱신 필요 (점수가 그래프에 반영되므로)
   */
  const updateAdos = useCallback(async (examId: string, scores: AdosUpdateRequest) => {
    try {
      const updatedAdos = await examReportApi.updateAdos(examId, scores);
      setCurrentAdosDetail(updatedAdos);

      // 점수가 바뀌었으므로 그래프도 최신화
      if (selectedPatient?.childId) {
        const newGraphs = await examReportApi.getAdosGraphs(selectedPatient.childId);
        setAdosGraphs(newGraphs);
      }
      return updatedAdos;
    } catch (error) {
      console.error("❌ [ADOS] 수정 실패:", error);
      throw error;
    }
  }, [selectedPatient]);

  /**
   * 환자 선택 핸들러
   */
  const selectPatient = useCallback((patient: PatientDto) => {
    // 1. 환자 상세 정보 설정
    const patientDetail = doctorApi.getPatientDetailFromDto(patient);
    setSelectedPatient(patientDetail);

    // 2. [테스트용] 하드코딩된 hospitalChildrenId 사용
    // TODO: 테스트 후 원래 로직으로 복원 필요
    // const targetId = patient.hospitalChildrenId || patient.childId;
    const targetId = 'db9d306a-9948-4823-917b-c47e277a6a44'; // 테스트용 하드코딩

    console.log(`📋 환자 선택됨: ${patient.name}`);
    console.log(`👉 사용된 ID: ${targetId} (테스트용 하드코딩)`);

    // 3. 통합 데이터 로딩
    if (targetId) {
      loadExamReportInitialData(targetId);
    }

    setSidebarOpen(false);
  }, [loadExamReportInitialData]);

  /**
   * 대기열 조회 (오늘 날짜)
   */
  useEffect(() => {
    const fetchWaitingList = async () => {
      setIsLoading(true);
      try {
        const today = new Date().toISOString().split('T')[0];
        const response = await doctorApi.searchPatients({
          page: 0,
          size: 100,
          date: today,
          effectiveDate: today
        });

        if (response.code === 200 && response.data?.childResponses?.length > 0) {
          const patients = response.data.childResponses;
          setWaitingList(patients);
          // 첫 번째 환자 자동 선택
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

  // UI 액션들
  const toggleSidebar = () => setSidebarOpen((prev) => !prev);

  return {
    states: {
      isSidebarOpen,
      isVideoModalOpen,
      isAdosModalOpen,
      selectedPatient,
      waitingList,
      isLoading,
      // API Data
      examReportData,
      examVideoList,
      currentVideoData,
      adosGraphs,
      currentAdosDetail,
      isExamReportLoading,
    },
    actions: {
      toggleSidebar,
      setVideoModalOpen,
      setAdosModalOpen,
      selectPatient,
      selectVideo,
      loadAdosDetail,
      updateAdos,
    },
  };
};