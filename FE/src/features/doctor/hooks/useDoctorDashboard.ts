//src/features/doctor/hooks/useDoctorDashboard.ts
import { useState, useEffect, useCallback } from "react";
import { doctorApi } from "../api/doctorApi";
import type { PatientDetailFull, PatientDto } from "../types/doctor";

export const useDoctorDashboard = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [isVideoModalOpen, setVideoModalOpen] = useState(false);
  const [isAdosModalOpen, setAdosModalOpen] = useState(false);

  const [waitingList, setWaitingList] = useState<PatientDto[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientDetailFull | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 환자 선택 함수
  const selectPatient = useCallback((patient: PatientDto) => {
    const patientDetail = doctorApi.getPatientDetailFromDto(patient);
    setSelectedPatient(patientDetail);
    console.log("📋 환자 선택:", patient.name);
  }, []);

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
    },
    actions: {
      toggleSidebar,
      setVideoModalOpen,
      setAdosModalOpen,
      selectPatient,
    },
  };
};