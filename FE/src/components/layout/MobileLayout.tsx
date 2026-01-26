import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Home, FileText, User } from 'lucide-react'; // 아이콘 임포트

const MobileLayout = () => {

  return (
    // 1. 컨테이너: 1600x1000 사이즈, 중앙 정렬, 배경색 설정
    <div className="flex flex-col h-[1000px] max-w-[1600px] mx-auto bg-gradient-to-br from-[#f9f8fc] via-[#E6E6FA] to-[#d1c7ee] shadow-2xl relative overflow-hidden border-x border-gray-200">
      <Outlet />

    </div>
  );
};

export default MobileLayout;