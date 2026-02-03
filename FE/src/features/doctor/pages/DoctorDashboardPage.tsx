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

  return (
    // 전체 화면 컨테이너 (헤더 고정, 바디 스크롤 구조)
    <div className="h-screen w-screen bg-[#808080] flex flex-col overflow-hidden font-['Gulim'] text-[11px]">
      {/* 1. Header (고정됨) */}
      <header className="bg-[#000080] text-white h-[35px] flex items-center px-2 justify-between shrink-0 z-50">
        <span className="font-bold">
          ASD Clinical Support System - Data Terminal v1.0
        </span>
        <div className="flex gap-1">{/* ... 버튼들 ... */}</div>
      </header>

      {/* 2. Main Grid Layout (여기를 수정!) */}
      <main
        className={cn(
          "flex-1 grid gap-[2px] p-[2px] bg-[#808080]",
          "grid-cols-[220px_180px_1fr_340px_260px]",
          "grid-rows-[1fr]",

          // [수정 포인트 1] overflow-hidden -> overflow-y-auto (세로 스크롤 허용)
          "overflow-y-auto",

          // [수정 포인트 2] 최소 높이 지정 (화면이 이보다 작아지면 스크롤 발생)
          // 내부 패널들의 최소 높이 합계를 고려해 설정 (예: 720px)
          "min-h-[720px]",
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

        {/* Col 3: 중앙 분석 */}
        <div className="row-span-full h-full overflow-hidden">
          <CentralAnalysisPanel
            onExpandVideo={() => actions.setVideoModalOpen(true)}
          />
        </div>

        {/* Col 4: 그래프 */}
        <div className="row-span-full h-full overflow-hidden">
          <TrendChartPanel />
        </div>

        {/* Col 5: AI 결과 */}
        <div className="row-span-full h-full overflow-hidden">
          <AiDiagnosisPanel
            onExpandAdos={() => actions.setAdosModalOpen(true)}
          />
        </div>
      </main>

      {/* ... Modals ... */}
      {/* 모달은 페이지 구조 밖에 있으므로 스크롤 영향 안 받음 (정상) */}
      {states.isVideoModalOpen && (
        <VideoModal onClose={() => actions.setVideoModalOpen(false)} />
      )}
      {states.isAdosModalOpen && (
        <AdosModal onClose={() => actions.setAdosModalOpen(false)} />
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
