// src/features/doctor/hooks/useDoctorDashboard.ts
import { useState, useEffect } from "react";
import { doctorApi } from "../api/doctorApi";
import type { PatientDetailFull } from "../types/doctor";

export const useDoctorDashboard = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [isVideoModalOpen, setVideoModalOpen] = useState(false);
  const [isAdosModalOpen, setAdosModalOpen] = useState(false);

  const [selectedPatient, setSelectedPatient] =
    useState<PatientDetailFull | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 초기 데이터 로드 (Mock Data)
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const data = await doctorApi.getPatientDetail("dummy-child-id");
        setSelectedPatient(data);
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchInitialData();
  }, []);

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
      isLoading,
    },
    actions: {
      toggleSidebar,
      setVideoModalOpen,
      setAdosModalOpen,
    },
  };
};
