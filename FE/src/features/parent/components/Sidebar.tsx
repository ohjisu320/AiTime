// Sidebar.tsx
import type { DashboardData } from '../types/dashboard';

// 1. Props 인터페이스에 클릭 핸들러 추가
interface SidebarProps {
  childName: string;
  onCodeInputClick: () => void;
}

const Sidebar = ({ childName, onCodeInputClick }: SidebarProps) => {
  return (
    <aside className="w-64 flex flex-none flex-col sticky top-0 bg-white border-r border-gray-200 h-screen min-h-[1000px]">      <div className="h-24 px-6 pt-6 border-b border-gray-200 flex flex-col justify-start items-start shrink-0">
      <div className="inline-flex justify-start items-center gap-3">
        <div className="w-10 h-10 bg-gradient-to-b from-violet-400 to-violet-300 rounded-2xl flex justify-center items-center text-white font-bold text-lg">Ai</div>
        <div className="flex flex-col">
          <span className="text-gray-800 text-2xl font-bold leading-none tracking-tight">AiTime</span>
          <span className="text-gray-500 text-[10px] mt-1 uppercase font-semibold">Parent Dashboard</span>
        </div>
      </div>
    </div>

      <nav className="flex-1 px-4 pt-4 pb-4 flex flex-col gap-2">
        <div className="h-12 pl-4 bg-gradient-to-b from-indigo-100 to-indigo-50 rounded-2xl inline-flex items-center gap-3 cursor-pointer">
          <div className="text-indigo-600 font-bold">홈</div>
        </div>

        {/* 2. 초대 코드 입력 메뉴에 onClick 이벤트 연결 */}
        <div
          onClick={onCodeInputClick}
          className="h-12 pl-4 rounded-2xl inline-flex items-center gap-3 text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors"
        >
          <span>초대 코드 입력</span>
        </div>

        <div className="h-12 pl-4 rounded-2xl inline-flex items-center gap-3 text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors">
          <span>회원정보 수정</span>
        </div>

        <div className="mt-auto pt-4 border-t border-gray-200">
          <div className="h-32 px-4 pt-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl flex flex-col gap-3">
            <div className="inline-flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-200 rounded-full flex justify-center items-center text-white text-sm">👤</div>
              <div className="flex flex-col overflow-hidden">
                <span className="text-gray-800 text-sm font-bold truncate">이지현님</span>
                <span className="text-gray-500 text-[10px] truncate">{childName}의 부모님</span>
              </div>
            </div>
            <button className="h-9 w-full bg-white rounded-lg border border-gray-200 text-gray-600 text-xs font-medium hover:bg-gray-50 transition-colors">
              로그아웃
            </button>
          </div>
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;