// src/features/doctor/pages/DoctorDashboardPage.tsx
import { useState, useCallback, useMemo } from "react";
import { useDoctorDashboard } from "../hooks/useDoctorDashboard";
import PatientDetailPanel from "../components/panels/PatientDetailPanel";
import SessionListPanel from "../components/panels/SessionListPanel";
import CentralAnalysisPanel from "../components/panels/CentralAnalysisPanel";
import TrendChartPanel from "../components/panels/TrendChartPanel";
import AiDiagnosisPanel from "../components/panels/AiDiagnosisPanel";
import VideoModal from "../components/modals/VideoModal";
import AdosModal from "../components/modals/AdosModal";
import WaitingListSidebar from "../components/panels/WaitingListSidebar";
import DoctorLayout from "../components/layout/DoctorLayout";
import type { VideoAnalysisData } from "../types/doctor";
import type { AdosUpdateRequest } from "@/api/types/examReport.types";

const DEFAULT_ANALYSIS: VideoAnalysisData = {
  videoUrl: "",
  totalDuration: 60,
  timestamps: [],
};

export default function DoctorDashboardPage() {
  const { states, actions } = useDoctorDashboard();
  const patientAge = states.selectedPatient?.monthlyAge || 0;

  const analysisData: VideoAnalysisData = useMemo(() => {
    if (!states.currentVideoData) {
      return DEFAULT_ANALYSIS;
    }

    const videoData = states.currentVideoData;
    const maxEndTime = videoData.timestamps.reduce(
      (max, ts) => Math.max(max, ts.endS),
      0
    );
    const totalDuration = Math.max(maxEndTime + 5, 60);

    return {
      videoUrl: videoData.viewUrl,
      totalDuration,
      timestamps: videoData.timestamps.map((ts, idx) => ({
        id: idx + 1,
        type: "child-behavior" as const,
        label: `Trial ${ts.trialIndex}`,
        startTime: ts.startS,
        duration: ts.endS - ts.startS,
      })),
    };
  }, [states.currentVideoData]);

  const [videoStartTime, setVideoStartTime] = useState(0);

  const handleAdosSave = useCallback(async (examId: string, scores: AdosUpdateRequest) => {
    await actions.updateAdos(examId, scores);
  }, [actions]);

  const latestExamId = states.currentAdosDetail?.examId ||
    (states.examVideoList.length > 0 ? states.examVideoList[0].examId : undefined);

  return (
    // [수정] 기본 폰트 사이즈 13px로 증가
    <div className="h-screen w-screen bg-[#808080] flex flex-col overflow-hidden font-['Gulim'] text-[13px]">
      <main className="flex-1 overflow-hidden bg-[#808080] p-[2px]">
        <DoctorLayout
          panels={{
            "patient-detail": (
              <PatientDetailPanel
                patient={states.selectedPatient}
                toggleSidebar={actions.toggleSidebar}
              />
            ),
            "session-list": (
              <SessionListPanel
                examVideoList={states.examVideoList}
                onSelectVideo={actions.selectVideo}
                currentVideoExamId={states.currentVideoData?.examId}
              />
            ),
            "central-analysis": (
              <CentralAnalysisPanel
                analysisData={analysisData}
                onExpandVideo={(currentTime) => {
                  setVideoStartTime(currentTime);
                  actions.setVideoModalOpen(true);
                }}
              />
            ),
            "trend-chart": (
              <TrendChartPanel
                adosGraphs={states.adosGraphs}
              />
            ),
            "ai-diagnosis": (
              <AiDiagnosisPanel
                onExpandAdos={() => actions.setAdosModalOpen(true)}
                patientAge={patientAge}
                adosDetail={states.currentAdosDetail}
              />
            ),
          }}
        />
      </main>

      {states.isVideoModalOpen && (
        <VideoModal
          videoUrl={analysisData.videoUrl}
          startTime={videoStartTime}
          onClose={() => actions.setVideoModalOpen(false)}
        />
      )}

      {states.isAdosModalOpen && (
        <AdosModal
          onClose={() => actions.setAdosModalOpen(false)}
          patientAge={patientAge}
          adosDetail={states.currentAdosDetail}
          examId={latestExamId}
          onSave={handleAdosSave}
        />
      )}

      {states.isSidebarOpen && (
        <WaitingListSidebar
          isOpen={states.isSidebarOpen}
          onClose={actions.toggleSidebar}
          onSelectPatient={actions.selectPatient}
        />
      )}
    </div>
  );
}