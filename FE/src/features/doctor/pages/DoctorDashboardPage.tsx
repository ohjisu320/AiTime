import { useDoctorDashboard } from "../hooks/useDoctorDashboard";
import PatientDetailPanel from "../components/panels/PatientDetailPanel";
import SessionListPanel from "../components/panels/SessionListPanel";
import CentralAnalysisPanel from "../components/panels/CentralAnalysisPanel";
import TrendChartPanel from "../components/panels/TrendChartPanel";
import AiDiagnosisPanel from "../components/panels/AiDiagnosisPanel";
import VideoModal from "../components/modals/VideoModal";
import AdosModal from "../components/modals/AdosModal";
import WaitingListSidebar from "../components/panels/WaitingListSidebar";
import { cn } from "@/lib/utils";

export default function DoctorDashboardPage() {
  const { states, actions } = useDoctorDashboard();

  // [수정] patientAge 변수 정의 (선택된 환자가 없으면 0으로 처리)
  const patientAge = states.selectedPatient?.monthlyAge || 0;

  return (
    <div className="h-screen w-screen bg-[#808080] flex flex-col overflow-hidden font-['Gulim'] text-[11px]">
      {/* 1. Top Bar */}
      <header className="bg-[#000080] text-white h-[35px] flex items-center px-2 justify-between shrink-0">
        <span className="font-bold">
          ASD Clinical Support System - Data Terminal v1.0
        </span>
        <div className="flex gap-1">{/* 상단 버튼 영역 (필요시 추가) */}</div>
      </header>

      {/* 2. Main Grid Layout */}
      <main
        className={cn(
          "flex-1 grid gap-[2px] p-[2px] bg-[#808080]",
          "grid-cols-[220px_180px_1fr_340px_260px]",
          "grid-rows-[1fr]",
          "overflow-y-auto", // 세로 스크롤 허용
          "min-h-[720px]", // 최소 높이 확보
        )}
      >
        {/* Col 1: 환자 상세 */}
        <div className="row-span-full h-full overflow-hidden">
          <PatientDetailPanel
            patient={states.selectedPatient}
            toggleSidebar={actions.toggleSidebar}
          />
        </div>

        {/* Col 2: 세션 리스트 */}
        <div className="row-span-full h-full overflow-hidden">
          <SessionListPanel />
        </div>

        {/* Col 3: 중앙 분석 (체크리스트, 비디오, 타임라인) */}
        <div className="row-span-full h-full overflow-hidden">
          <CentralAnalysisPanel
            onExpandVideo={() => actions.setVideoModalOpen(true)}
          />
        </div>

        {/* Col 4: 그래프 사이드바 */}
        <div className="row-span-full h-full overflow-hidden">
          <TrendChartPanel />
        </div>

        {/* Col 5: AI 결과 및 ADOS */}
        <div className="row-span-full h-full overflow-hidden">
          {/* [수정] patientAge prop 전달 */}
          <AiDiagnosisPanel
            onExpandAdos={() => actions.setAdosModalOpen(true)}
            patientAge={patientAge}
          />
        </div>
      </main>

      {/* 3. Modals & Sidebar (조건부 렌더링) */}
      {/* [수정] VideoModal, AdosModal, WaitingListSidebar가 여기서 사용됨 */}
      {states.isVideoModalOpen && (
        <VideoModal onClose={() => actions.setVideoModalOpen(false)} />
      )}

      {states.isAdosModalOpen && (
        <AdosModal
          onClose={() => actions.setAdosModalOpen(false)}
          patientAge={patientAge} // [수정] patientAge prop 전달
        />
      )}

      {states.isSidebarOpen && (
        <WaitingListSidebar
          isOpen={states.isSidebarOpen}
          onClose={actions.toggleSidebar}
        />
      )}
    </div>
  );
}
