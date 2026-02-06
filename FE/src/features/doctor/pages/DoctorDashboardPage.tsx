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
import type { VideoAnalysisData, AnalysisTimestamp } from "../types/doctor";
import type { AdosUpdateRequest, PoseTimestamp, SimpleTimestamp, NonFacingTimestamp } from "@/api/types/examReport.types";

const DEFAULT_ANALYSIS: VideoAnalysisData = {
  videoUrl: "",
  totalDuration: 60,
  timestamps: [],
  rows: [
    { key: "parent", label: "부모 행동", color: "bg-gray-500" },
    { key: "child-vocal", label: "아이 음성", color: "bg-green-600" },
    { key: "child-behavior", label: "아이 행동", color: "bg-blue-600" },
  ],
};

export default function DoctorDashboardPage() {
  const { states, actions } = useDoctorDashboard();
  const patientAge = states.selectedPatient?.monthlyAge || 0;

  // [핵심 로직] API 데이터를 UI용 데이터로 변환 (타입별 분기 처리)
  const analysisData: VideoAnalysisData = useMemo(() => {
    if (!states.currentVideoData) {
      return DEFAULT_ANALYSIS;
    }

    const videoData = states.currentVideoData;
    const rawTimestamps = videoData.timestamps || [];
    const uiTimestamps: AnalysisTimestamp[] = [];
    let maxEndTime = 0;

    // 비디오 타입에 따른 데이터 매핑 전략
    rawTimestamps.forEach((ts, idx) => {
      const baseId = (idx + 1) * 10; // ID 충돌 방지용

      // 1. 동작 모방 (POSE_IMITATION)
      if (videoData.videoType === 'POSE_IMITATION') {
        const item = ts as PoseTimestamp;

        // (1) 부모 행동 (Parent)
        uiTimestamps.push({
          id: baseId + 1,
          type: "parent",
          label: `Trial ${item.trialIndex} (시연)`,
          startTime: item.parentStartTime,
          duration: item.parentEndTime - item.parentStartTime,
        });

        // (2) 아이 행동 (Child)
        uiTimestamps.push({
          id: baseId + 2,
          type: "child-behavior",
          label: `Trial ${item.trialIndex} (모방)`,
          startTime: item.childStartTime,
          duration: item.childEndTime - item.childStartTime,
        });

        maxEndTime = Math.max(maxEndTime, item.childEndTime);
      }

      // 2. 발화 모방 (SPEECH_IMITATION)
      else if (videoData.videoType === 'SPEECH_IMITATION') {
        const item = ts as SimpleTimestamp;

        uiTimestamps.push({
          id: baseId,
          type: "child-vocal", // 음성 라인에 표시
          label: `Trial ${item.trialIndex}`,
          startTime: item.trialStartS,
          duration: item.trialEndS - item.trialStartS,
        });

        maxEndTime = Math.max(maxEndTime, item.trialEndS);
      }

      // 3. 대면 호명 (NAME_FACING)
      else if (videoData.videoType === 'NAME_FACING') {
        const item = ts as SimpleTimestamp;

        uiTimestamps.push({
          id: baseId,
          type: "child-behavior", // 행동 라인에 표시
          label: `Trial ${item.trialIndex}`,
          startTime: item.trialStartS,
          duration: item.trialEndS - item.trialStartS,
        });

        maxEndTime = Math.max(maxEndTime, item.trialEndS);
      }

      // 4. 비대면 호명 (NAME_NON_FACING)
      else if (videoData.videoType === 'NAME_NON_FACING') {
        const item = ts as NonFacingTimestamp;

        // (1) 시각적 자극/트리거 (Parent 라인 활용)
        uiTimestamps.push({
          id: baseId + 1,
          type: "parent",
          label: `T${item.trialIndex} 자극`,
          startTime: item.triggerStartS,
          duration: item.triggerEndS - item.triggerStartS,
        });

        // (2) 호명/반응 (Child Vocal 또는 Behavior 라인 활용)
        // 여기서는 '호명(소리)' 구간이므로 child-vocal 쪽에 표시하거나 
        // 맥락에 따라 parent 라인에 '호명'으로 표시할 수도 있습니다.
        // 현재는 아이의 반응 구간이 명시적이지 않으므로 호명 구간을 표시합니다.
        uiTimestamps.push({
          id: baseId + 2,
          type: "child-vocal", // 혹은 'parent' (검사자 목소리이므로)
          label: `T${item.trialIndex} 호명`,
          startTime: item.voiceStartS,
          duration: item.voiceEndS - item.voiceStartS,
        });

        maxEndTime = Math.max(maxEndTime, item.voiceEndS);
      }
    });

    const totalDuration = Math.max(maxEndTime + 5, 60);

    // [동적 타임라인 설정] 비디오 타입별 행 구성
    // keys: "parent" | "child-vocal" | "child-behavior"
    let timelineRows: { key: string; label: string; color: string }[] = [];

    switch (videoData.videoType) {
      case 'POSE_IMITATION':
        timelineRows = [
          { key: "parent", label: "부모 시연", color: "bg-gray-500" },
          { key: "child-behavior", label: "아이 모방", color: "bg-blue-600" },
        ];
        break;
      case 'SPEECH_IMITATION':
        timelineRows = [
          { key: "child-vocal", label: "아이 발화", color: "bg-green-600" },
        ];
        break;
      case 'NAME_FACING':
        timelineRows = [
          { key: "child-behavior", label: "아이 반응", color: "bg-blue-600" },
        ];
        break;
      case 'NAME_NON_FACING':
        timelineRows = [
          { key: "parent", label: "자극 제시", color: "bg-gray-500" },
          { key: "child-vocal", label: "호명(청각)", color: "bg-yellow-600" }, // 구분을 위해 색상 변경
        ];
        break;
      default:
        // 기본값 (모두 표시)
        timelineRows = [
          { key: "parent", label: "부모 행동", color: "bg-gray-500" },
          { key: "child-vocal", label: "아이 음성", color: "bg-green-600" },
          { key: "child-behavior", label: "아이 행동", color: "bg-blue-600" },
        ];
    }

    return {
      videoUrl: videoData.viewUrl,
      totalDuration,
      timestamps: uiTimestamps,
      rows: timelineRows,
    };
  }, [states.currentVideoData]);

  const [videoStartTime, setVideoStartTime] = useState(0);

  const handleAdosSave = useCallback(async (examId: string, scores: AdosUpdateRequest) => {
    await actions.updateAdos(examId, scores);
  }, [actions]);

  const latestExamId = states.currentAdosDetail?.examId ||
    (states.examVideoList.length > 0 ? states.examVideoList[0].examId : undefined);

  return (
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