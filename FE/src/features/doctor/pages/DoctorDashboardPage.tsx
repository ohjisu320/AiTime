import { useState, useCallback } from "react";
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

// [이동] 데이터 정의를 부모 페이지로 이동
const MOCK_ANALYSIS: VideoAnalysisData = {
  videoUrl:
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
  totalDuration: 60,
  timestamps: [
    { id: 1, type: "parent", label: "부모 지시", startTime: 5, duration: 3 },
    { id: 2, type: "child-vocal", label: "옹알이", startTime: 12, duration: 4 },
    {
      id: 3,
      type: "child-behavior",
      label: "손 흔들기",
      startTime: 25,
      duration: 5,
    },
    { id: 4, type: "child-vocal", label: "울음", startTime: 40, duration: 2 },
    { id: 5, type: "parent", label: "반응 유도", startTime: 50, duration: 5 },
  ],
};

export default function DoctorDashboardPage() {
  const { states, actions } = useDoctorDashboard();
  const patientAge = states.selectedPatient?.monthlyAge || 0;

  // [추가] 모달로 전달할 영상 시작 시간 상태
  const [videoStartTime, setVideoStartTime] = useState(0);

  // ADOS 저장 핸들러
  const handleAdosSave = useCallback(async (examId: string, scores: AdosUpdateRequest) => {
    await actions.updateAdos(examId, scores);
  }, [actions]);

  // 최신 examId 가져오기
  const latestExamId = states.currentAdosDetail?.examId ||
    (states.examVideoList.length > 0 ? states.examVideoList[0].examId : undefined);

  return (
    <div className="h-screen w-screen bg-[#808080] flex flex-col overflow-hidden font-['Gulim'] text-[11px]">
      <main className="flex-1 overflow-hidden bg-[#808080] p-[2px]">
        <DoctorLayout
          panels={{
            "patient-detail": (
              <PatientDetailPanel
                patient={states.selectedPatient}
                toggleSidebar={actions.toggleSidebar}
              />
            ),
            "session-list": <SessionListPanel />,
            "central-analysis": (
              <CentralAnalysisPanel
                analysisData={MOCK_ANALYSIS}
                onExpandVideo={(currentTime) => {
                  setVideoStartTime(currentTime);
                  actions.setVideoModalOpen(true);
                }}
              />
            ),
            "trend-chart": <TrendChartPanel adosGraphs={states.adosGraphs} />,
            "ai-diagnosis": (
              <AiDiagnosisPanel
                onExpandAdos={() => actions.setAdosModalOpen(true)}
                patientAge={patientAge}
              />
            ),
          }}
        />
      </main>

      {/* Modals */}
      {states.isVideoModalOpen && (
        <VideoModal
          // [수정] URL과 시작 시간 전달
          videoUrl={MOCK_ANALYSIS.videoUrl}
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

