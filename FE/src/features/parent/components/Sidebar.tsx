// Sidebar.tsx
import { useNavigate } from 'react-router-dom';
import { logoutUser } from '../../auth/api/authApi';
import { getCurrentUserFromToken } from '@/utils/jwtUtils';
import parentLogo from '@/assets/parentLogo.svg';

// 1. Props 인터페이스에 클릭 핸들러 추가
interface SidebarProps {
  childName: string;
  onCodeInputClick: () => void;
}

const Sidebar = ({ childName, onCodeInputClick }: SidebarProps) => {
  const navigate = useNavigate();

  // JWT 토큰에서 부모 정보 추출
  const userInfo = getCurrentUserFromToken();
  const parentName = userInfo?.sub || '부모님'; // sub에 username이 들어있음

  const handleLogout = async () => {

    try {
      await logoutUser();
    } catch (e) {
      console.warn("Force logging out despite API error", e);
    } finally {
      // Client-side cleanup
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      // Redirect to Root
      navigate('/');
    }
  };
  return (
    <aside className="w-64 flex flex-none flex-col sticky top-0 bg-white border-r border-gray-200 h-screen">
      <div className="h-24 px-6 pt-6 border-b border-gray-200 flex flex-col justify-start items-start shrink-0">
        <div className="inline-flex justify-start items-center gap-3 cursor-pointer" onClick={() => navigate('/parent/select-profile')}>
          {/* 홈 버튼 */}
          <img src={parentLogo} alt="parentLogo" className="w-[45px] h-[45px]" />

          <div className="flex flex-col">
            <span className="text-gray-800 text-2xl font-bold leading-none tracking-tight">AiTime</span>
            <span className="text-gray-500 text-[10px] mt-1 uppercase font-semibold">Parent Dashboard</span>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 pt-4 pb-4 flex flex-col gap-2 overflow-y-auto">

        {/* 홈 버튼 */}
        <div className="h-12 pl-4 bg-gradient-to-b from-indigo-100 to-indigo-50 rounded-2xl inline-flex items-center gap-3 cursor-pointer" onClick={() => navigate('/parent/dashboard')} >
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
          <div onClick={() => navigate('/parent/mypage/edit')}>
            <span>회원정보 수정</span>
          </div>
        </div>

        {/* 로그아웃 섹션 - mt-auto로 맨 아래 배치 */}
        <div className="mt-auto pt-4 border-t border-gray-200 shrink-0">
          <div className="h-32 px-4 pt-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl flex flex-col gap-3">
            <div className="inline-flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-200 rounded-full flex justify-center items-center text-white text-sm">👤</div>
              <div className="flex flex-col overflow-hidden">
                <span className="text-gray-800 text-sm font-bold truncate">{parentName}님</span>
                <span className="text-gray-500 text-[10px] truncate">{childName}의 부모님</span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="h-9 w-full bg-white rounded-lg border border-gray-200 text-gray-600 text-xs font-medium hover:bg-gray-50 transition-colors"
            >
              로그아웃
            </button>
          </div>
        </div>
      </nav>
    </aside >
  );
};

export default Sidebar;