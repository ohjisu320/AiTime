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

// 기본 분석 데이터 (API 데이터 없을 때 폴백)
const DEFAULT_ANALYSIS: VideoAnalysisData = {
  videoUrl: "",
  totalDuration: 60,
  timestamps: [],
};

export default function DoctorDashboardPage() {
  const { states, actions } = useDoctorDashboard();
  const patientAge = states.selectedPatient?.monthlyAge || 0;

  // [핵심] API로부터 받은 currentVideoData를 VideoAnalysisData 형식으로 변환
  const analysisData: VideoAnalysisData = useMemo(() => {
    if (!states.currentVideoData) {
      return DEFAULT_ANALYSIS;
    }

    const videoData = states.currentVideoData;
    // 비디오 총 길이 계산 (timestamps 기반 추정, 마지막 endS 사용)
    const maxEndTime = videoData.timestamps.reduce(
      (max, ts) => Math.max(max, ts.endS),
      0
    );
    const totalDuration = Math.max(maxEndTime + 5, 60); // 최소 60초 또는 마지막 타임스탬프 + 여유

    return {
      videoUrl: videoData.viewUrl,
      totalDuration,
      timestamps: videoData.timestamps.map((ts, idx) => ({
        id: idx + 1,
        type: "child-behavior" as const, // API 타임스탬프를 child-behavior 행에 표시
        label: `Trial ${ts.trialIndex}`,
        startTime: ts.startS,
        duration: ts.endS - ts.startS,
      })),
    };
  }, [states.currentVideoData]);

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
            // [수정됨] SessionListPanel에 필요한 props 전달
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
            // [수정됨] TrendChartPanel에 그래프 데이터 전달
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

      {/* Modals */}
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
          waitingList={states.waitingList}
        />
      )}
    </div>
  );
}