//src/features/doctor/hooks/useDoctorDashboard.ts
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
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [isVideoModalOpen, setVideoModalOpen] = useState(false);
  const [isAdosModalOpen, setAdosModalOpen] = useState(false);

  const [waitingList, setWaitingList] = useState<PatientDto[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientDetailFull | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // ============================================================
  // 검사 리포트 관련 상태 (새로 추가)
  // ============================================================
  const [examReportData, setExamReportData] = useState<ExamReportInitialData | null>(null);
  const [examVideoList, setExamVideoList] = useState<ExamVideoListItem[]>([]);
  const [currentVideoData, setCurrentVideoData] = useState<VideoPresignView | null>(null);
  const [adosGraphs, setAdosGraphs] = useState<AdosGraphs | null>(null);
  const [currentAdosDetail, setCurrentAdosDetail] = useState<AdosDetail | null>(null);
  const [isExamReportLoading, setIsExamReportLoading] = useState(false);

  // hospitalChildrenId 상태 (환아-병원 매핑 ID)
  // TODO: 현재는 childId를 사용하지만, 실제 hospitalChildrenId가 API에서 제공해야 함
  const [currentHospitalChildrenId, setCurrentHospitalChildrenId] = useState<string | null>(null);

  // ============================================================
  // 환아 선택 시 초기 데이터 로딩
  // ============================================================
  const loadExamReportInitialData = useCallback(async (hospitalChildrenId: string) => {
    setIsExamReportLoading(true);
    try {
      console.log("📡 [ExamReport] 초기 데이터 로딩 시작:", hospitalChildrenId);

      const data = await examReportApi.getExamReportsInitial(hospitalChildrenId);

      setExamReportData(data);
      setExamVideoList(data.examVideoList);
      setAdosGraphs(data.adosGraphs);
      setCurrentAdosDetail(data.latestAdosDetail);

      // 최신 POSE_IMITATION 비디오가 있으면 설정
      if (data.latestPoseImitationVideo) {
        setCurrentVideoData(data.latestPoseImitationVideo);
      }

      console.log("✅ [ExamReport] 초기 데이터 로딩 완료");
    } catch (error: any) {
      console.error("❌ [ExamReport] 초기 데이터 로딩 실패:", error);
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

  // ============================================================
  // 비디오 선택 (presign-view 호출)
  // ============================================================
  const selectVideo = useCallback(async (videoId: string) => {
    try {
      console.log("📡 [Video] 비디오 선택:", videoId);
      const videoData = await examReportApi.getVideoPresignView(videoId);
      setCurrentVideoData(videoData);
      console.log("✅ [Video] 비디오 데이터 로딩 완료");
    } catch (error) {
      console.error("❌ [Video] 비디오 데이터 로딩 실패:", error);
    }
  }, []);

  // ============================================================
  // ADOS 상세 조회 (특정 검사 기준)
  // ============================================================
  const loadAdosDetail = useCallback(async (examId: string) => {
    try {
      console.log("📡 [ADOS] 상세 조회:", examId);
      const adosDetail = await examReportApi.getAdosDetail(examId);
      setCurrentAdosDetail(adosDetail);
      console.log("✅ [ADOS] 상세 조회 완료");
    } catch (error) {
      console.error("❌ [ADOS] 상세 조회 실패:", error);
    }
  }, []);

  // ============================================================
  // ADOS 수정
  // ============================================================
  const updateAdos = useCallback(async (examId: string, scores: AdosUpdateRequest) => {
    try {
      console.log("📡 [ADOS] 수정 요청:", examId, scores);
      const updatedAdos = await examReportApi.updateAdos(examId, scores);
      setCurrentAdosDetail(updatedAdos);
      console.log("✅ [ADOS] 수정 완료");
      return updatedAdos;
    } catch (error) {
      console.error("❌ [ADOS] 수정 실패:", error);
      throw error;
    }
  }, []);

  // ============================================================
  // 환자 선택 함수 (기존 + 초기 데이터 로딩 추가)
  // ============================================================
  const selectPatient = useCallback((patient: PatientDto) => {
    const patientDetail = doctorApi.getPatientDetailFromDto(patient);
    setSelectedPatient(patientDetail);
    console.log("📋 환자 선택:", patient.name);

    // TODO: 실제로는 hospitalChildrenId를 사용해야 함
    // 현재는 childId를 임시로 사용
    const hospitalChildrenId = patient.childId;
    setCurrentHospitalChildrenId(hospitalChildrenId);

    // 초기 데이터 로딩
    loadExamReportInitialData(hospitalChildrenId);
  }, [loadExamReportInitialData]);

  // 오늘 날짜 구하기 (YYYY-MM-DD)
  const getTodayDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  // 전체 환자 목록 조회 및 첫 환자 자동 선택
  useEffect(() => {
    const fetchWaitingList = async () => {
      setIsLoading(true);
      try {
        const today = getTodayDate();
        console.log("📡 [API] 대기열 조회 요청 - 날짜:", today);

        // API 명세에 맞춰 date 파라미터 추가
        const response = await doctorApi.searchPatients({
          page: 0,
          size: 100,
          date: today,
          effectiveDate: today
        });

        if (response.code === 200 && response.data?.childResponses?.length > 0) {
          const patients = response.data.childResponses;
          console.log("📡 [API] 대기열 조회 성공:", patients.length, "명");
          setWaitingList(patients);
          // 첫 번째 환자 자동 선택
          selectPatient(patients[0]);
        } else {
          console.warn("📡 [API] 대기 환자 없음");
          setWaitingList([]);
          setSelectedPatient(null);
        }
      } catch (error: any) {
        console.error("📡 [API] 대기열 조회 실패:", error);

        // 인증 에러(500) 처리 로그
        if (error.response?.status === 500 && error.response?.data?.trace?.includes("UserPrincipal")) {
          console.error("🚨 [CRITICAL] 서버에서 사용자 정보를 찾을 수 없습니다. (NullPointerException)");
          console.error("👉 조치방법: 로그아웃 후 다시 로그인하여 새 토큰을 발급받아보세요.");
        }

        setWaitingList([]);
        setSelectedPatient(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWaitingList();
  }, [selectPatient]);

  const toggleSidebar = () => setSidebarOpen((prev) => !prev);

  // ESC 키 이벤트 핸들러
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setVideoModalOpen(false);
        setAdosModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, []);

  return {
    states: {
      isSidebarOpen,
      isVideoModalOpen,
      isAdosModalOpen,
      selectedPatient,
      waitingList,
      isLoading,
      // 새로 추가된 상태
      examReportData,
      examVideoList,
      currentVideoData,
      adosGraphs,
      currentAdosDetail,
      isExamReportLoading,
      currentHospitalChildrenId,
    },
    actions: {
      toggleSidebar,
      setVideoModalOpen,
      setAdosModalOpen,
      selectPatient,
      // 새로 추가된 액션
      selectVideo,
      loadAdosDetail,
      updateAdos,
      loadExamReportInitialData,
    },
  };
};