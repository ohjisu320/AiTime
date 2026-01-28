import { useParams } from "react-router-dom";

// ✅ 분리한 컴포넌트들 Import (경로가 정확한지 확인해주세요)
// 폴더 구조가 features/doctor/pages 와 features/doctor/components/report 라면 아래 경로가 맞습니다.
import ReportSidebar from "../components/report/ReportSidebar"; 
import TrendChartSection from "../components/report/TrendChartSection";
import BalanceChartSection from "../components/report/BalanceChartSection";
import ExamHistoryTable from "../components/report/ExamHistoryTable";

export default function DoctorExamReportPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="flex min-h-screen bg-[#F5F6F8] font-['Pretendard']">
      {/* 1. 사이드바 (props 전달) */}
      <ReportSidebar patientId={id} patientName="박지우" />

      {/* 2. 메인 컨텐츠 */}
      <main className="flex-1 flex flex-col min-w-0 overflow-auto">
        
        {/* 헤더 */}
        <header className="px-10 py-8 flex items-center justify-between bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-gray-900">
              상세 분석 리포트
            </h1>
            <span className="px-4 py-1.5 bg-green-50 text-green-600 text-sm font-bold rounded-full border border-green-100">
              분석 완료
            </span>
          </div>
          <span className="text-base text-gray-400 font-medium">
            최근 업데이트: 2026.01.19
          </span>
        </header>

        {/* 컨텐츠 영역 (너비 확대: max-w-[1600px]) */}
        <div className="p-10 space-y-8 max-w-[1600px] mx-auto w-full h-full">
          
          {/* 상단 그래프 영역 (높이 균형 맞춤) */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 h-auto">
            <TrendChartSection />
            <BalanceChartSection />
          </div>

          {/* 하단 테이블 영역 */}
          <ExamHistoryTable />
          
          {/* 하단 여백 확보 */}
          <div className="h-10"></div>
        </div>
      </main>
    </div>
  );
}