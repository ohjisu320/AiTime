// src/features/doctor/pages/DoctorDashboardPage.tsx
import { useState, useMemo } from "react";
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
  // 1. Hook을 통해 API 상태와 액션 가져오기
  const { states, actions } = useDoctorDashboard();

  // 환자 나이 (개월 수) - ADOS 필터링용
  const patientAge = states.selectedPatient?.monthlyAge || 0;

  // 2. [Data Transformation] API의 VideoPresignView 데이터를 UI용 VideoAnalysisData로 변환
  const analysisData: VideoAnalysisData = useMemo(() => {
    if (!states.currentVideoData) {
      return DEFAULT_ANALYSIS;
    }

    const videoData = states.currentVideoData;

    // 타임스탬프가 없는 경우 처리
    const timestamps = videoData.timestamps || [];

    // 비디오 총 길이 추정 (마지막 타임스탬프 + 5초 여유 혹은 최소 60초)
    const maxEndTime = timestamps.reduce(
      (max, ts) => Math.max(max, ts.endS),
      0
    );
    const totalDuration = Math.max(maxEndTime + 5, 60);

    return {
      videoUrl: videoData.viewUrl, // Presigned URL
      totalDuration,
      timestamps: timestamps.map((ts, idx) => ({
        id: idx + 1,
        // API의 trialIndex를 라벨로 사용
        label: `Trial ${ts.trialIndex}`,
        // 시각화 로직: 모든 마커를 'child-behavior' 라인에 표시 (필요시 type 분기 가능)
        type: "child-behavior",
        startTime: ts.startS,
        duration: ts.endS - ts.startS,
      })),
    };
  }, [states.currentVideoData]);

  // 비디오 모달용 시작 시간 상태
  const [videoStartTime, setVideoStartTime] = useState(0);

  // ADOS 저장 핸들러 (현재 API 미지원이나 확장성 고려)
  const handleAdosSave = async (examId: string, scores: AdosUpdateRequest) => {
    await actions.updateAdos(examId, scores);
  };

  // 최신 Exam ID 추출 (ADOS 모달용)
  const latestExamId = states.currentAdosDetail?.examId ||
    (states.examVideoList.length > 0 ? states.examVideoList[0].examId : undefined);

  return (
    <div className="h-screen w-screen bg-[#808080] flex flex-col overflow-hidden font-['Gulim'] text-[11px]">
      <main className="flex-1 overflow-hidden bg-[#808080] p-[2px]">
        {/* 로딩 인디케이터 (데이터 패칭 중일 때 오버레이) */}
        {states.isExamReportLoading && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/20 pointer-events-none">
            <div className="bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] px-4 py-2 shadow-lg">
              <span className="font-bold">데이터 조회 중...</span>
            </div>
          </div>
        )}

        <DoctorLayout
          panels={{
            // 1. 환자 상세 정보 패널
            "patient-detail": (
              <PatientDetailPanel
                patient={states.selectedPatient}
                toggleSidebar={actions.toggleSidebar}
              />
            ),
            // 2. 검사 세션 목록 패널
            "session-list": (
              <SessionListPanel
                examVideoList={states.examVideoList}
                onSelectVideo={actions.selectVideo} // 비디오 클릭 시 API 호출 트리거
                currentVideoExamId={states.currentVideoData?.examId} // 현재 선택된 검사 하이라이팅
              />
            ),
            // 3. 중앙 비디오 분석 패널
            "central-analysis": (
              <CentralAnalysisPanel
                analysisData={analysisData}
                onExpandVideo={(currentTime) => {
                  setVideoStartTime(currentTime);
                  actions.setVideoModalOpen(true);
                }}
              />
            ),
            // 4. ADOS 추이 그래프 패널
            "trend-chart": (
              <TrendChartPanel
                adosGraphs={states.adosGraphs} // /ados-graphs API 데이터 전달
              />
            ),
            // 5. 최신 ADOS 상세 진단 패널
            "ai-diagnosis": (
              <AiDiagnosisPanel
                onExpandAdos={() => actions.setAdosModalOpen(true)}
                patientAge={patientAge}
                adosDetail={states.currentAdosDetail} // /ados API 데이터 전달
              />
            ),
          }}
        />
      </main>

      {/* --- Modals --- */}

      {/* 확대된 비디오 모달 */}
      {states.isVideoModalOpen && (
        <VideoModal
          videoUrl={analysisData.videoUrl}
          startTime={videoStartTime}
          onClose={() => actions.setVideoModalOpen(false)}
        />
      )}

      {/* ADOS 상세 입력/수정 모달 */}
      {states.isAdosModalOpen && (
        <AdosModal
          onClose={() => actions.setAdosModalOpen(false)}
          patientAge={patientAge}
          adosDetail={states.currentAdosDetail}
          examId={latestExamId}
          onSave={handleAdosSave}
        />
      )}

      {/* 환자 대기열 사이드바 */}
      <WaitingListSidebar
        isOpen={states.isSidebarOpen}
        onClose={actions.toggleSidebar}
        onSelectPatient={actions.selectPatient} // 선택 시 useDoctorDashboard의 로직 실행
      />
    </div>
  );
}