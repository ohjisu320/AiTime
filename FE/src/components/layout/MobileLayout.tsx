import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Home, FileText, User } from 'lucide-react'; // 아이콘 임포트

const MobileLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // 현재 경로가 버튼의 경로와 일치하는지 확인하는 함수
  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    // 1. 컨테이너: 요청하신 1600x1000 사이즈, 중앙 정렬, 배경색 설정
    <div className="flex flex-col h-[1000px] max-w-[1600px] mx-auto bg-gradient-to-br from-[#f9f8fc] via-[#E6E6FA] to-[#d1c7ee] shadow-2xl relative overflow-hidden border-x border-gray-200">
      
      {/* 2. 헤더 (임시): AiTime 로고 */}
      <header className="h-16 bg-white/80 backdrop-blur-sm border-b flex items-center justify-center font-bold text-[#9D8AD6] text-xl z-10 flex-none">
        AiTime
      </header>

      {/* 3. 메인 컨텐츠 영역: 실제 페이지가 들어가는 곳 (스크롤 가능) */}
      <main className="flex-1 overflow-y-auto scrollbar-hide p-4">
        <Outlet />
      </main>

      {/* 4. 하단 탭바: 네비게이션 버튼 */}
      <nav className="h-24 bg-white border-t flex justify-around items-center text-xs text-gray-500 pb-4 safe-area-bottom z-10 flex-none shadow-[0_-1px_10px_rgba(0,0,0,0.05)]">
        
        {/* 홈 버튼 */}
        <button 
          onClick={() => navigate('/parent/dashboard')}
          className={`flex flex-col items-center gap-1 p-3 rounded-2xl transition-colors ${
            isActive('/parent/dashboard') ? 'text-[#9D8AD6] bg-purple-50' : 'hover:text-[#9D8AD6] hover:bg-gray-50'
          }`}
        >
          <Home className="w-7 h-7" />
          <span className="font-medium text-sm">홈</span>
        </button>

        {/* 검사 버튼 */}
        <button 
          onClick={() => navigate('/parent/exam')}
          className={`flex flex-col items-center gap-1 p-3 rounded-2xl transition-colors ${
            isActive('/parent/exam') ? 'text-[#9D8AD6] bg-purple-50' : 'hover:text-[#9D8AD6] hover:bg-gray-50'
          }`}
        >
          <FileText className="w-7 h-7" />
          <span className="font-medium text-sm">검사</span>
        </button>

        {/* 내 정보 버튼 (임시 경로) */}
        <button 
          onClick={() => navigate('/parent/profile')}
          className={`flex flex-col items-center gap-1 p-3 rounded-2xl transition-colors ${
            isActive('/parent/profile') ? 'text-[#9D8AD6] bg-purple-50' : 'hover:text-[#9D8AD6] hover:bg-gray-50'
          }`}
        >
          <User className="w-7 h-7" />
          <span className="font-medium text-sm">내 정보</span>
        </button>

      </nav>
    </div>
  );
};

export default MobileLayout;