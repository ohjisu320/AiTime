import { useNavigate } from "react-router-dom";
import { LayoutDashboard, ArrowLeft, User } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ReportSidebarProps {
  patientId?: string;
  patientName: string;
}

export default function ReportSidebar({
  patientId,
  patientName,
}: ReportSidebarProps) {
  const navigate = useNavigate();

  return (
    <aside className="w-[320px] bg-white border-r border-gray-200 flex flex-col h-screen sticky top-0 shrink-0 z-20 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
      {/* 1. 환자 프로필 영역 (크기 확대) */}
      <div className="p-10 flex flex-col items-center text-center border-b border-gray-100 bg-gray-50/30">
        <div className="w-32 h-32 bg-gradient-to-br from-blue-100 to-indigo-100 text-[#5A55D6] rounded-full flex items-center justify-center text-5xl mb-6 shadow-sm border-4 border-white">
          👶
        </div>
        <h2 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">
          {patientName}
        </h2>
        <div className="flex items-center gap-2 mb-6">
          <span className="px-3 py-1 bg-blue-50 text-blue-600 text-sm font-bold rounded-md">
            남아
          </span>
          <span className="text-gray-500 text-base font-medium">15개월</span>
        </div>
        <div className="w-full bg-white border border-gray-200 rounded-xl p-4 text-left shadow-sm">
          <p className="text-xs text-gray-400 font-bold uppercase mb-1">
            Chart No.
          </p>
          <p className="text-sm text-gray-700 font-mono truncate font-medium">
            {patientId || "Unknown"}
          </p>
        </div>
      </div>

      {/* 2. 네비게이션 버튼 영역 */}
      <div className="p-8 flex-1 space-y-4">
        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 px-2">
          Menu
        </p>

        <Button
          onClick={() => navigate("/doctor/dashboard")}
          className="w-full justify-start gap-4 h-14 text-lg font-bold bg-[#5A55D6] hover:bg-[#4844b8] text-white shadow-md transition-all rounded-xl"
        >
          <LayoutDashboard className="w-6 h-6" />
          대시보드 홈
        </Button>

        <Button
          onClick={() => navigate(-1)}
          variant="outline"
          className="w-full justify-start gap-4 h-14 text-lg font-medium text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900 transition-colors rounded-xl"
        >
          <ArrowLeft className="w-6 h-6" />
          이전 페이지
        </Button>
      </div>

      {/* 3. 하단 의사 정보 */}
      <div className="p-8 mt-auto border-t border-gray-50">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-gray-500">
            <User className="w-6 h-6" />
          </div>
          <div>
            <p className="text-base font-bold text-gray-800">김의사 선생님</p>
            <p className="text-sm text-gray-400">소아정신과 전문의</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
