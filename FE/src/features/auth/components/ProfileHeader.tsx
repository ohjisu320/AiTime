import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import parentLogo from '@/assets/parentLogo.svg';

export default function ProfileHeader() {
  const navigate = useNavigate();

  const handleLogout = () => {
    // 1. (필요시) 로컬 스토리지나 쿠키의 토큰 삭제 로직 추가
    // localStorage.removeItem("accessToken");

    // 2. 로그인 페이지로 이동
    navigate("/login"); // 혹은 "/"
  };

  return (
    <header className="w-full px-8 py-8 flex justify-between items-center">
      <div className="flex items-center gap-3" onClick={() => navigate('/parent/select-profile')}>
        {/* 홈 버튼 */}
        <img src={parentLogo} alt="parentLogo" className="w-[45px] h-[45px]" />

        {/* 로고 텍스트 */}
        <span className="text-3xl font-bold text-gray-800 tracking-tight">
          AiTime
        </span>
      </div>

      {/* 우측 버튼 그룹 */}
      <div className="flex items-center gap-4">
        {/* 로그아웃 버튼 (회색 톤으로 보조 버튼 느낌) */}
        <Button
          variant="ghost"
          onClick={handleLogout}
          className="text-gray-500 hover:text-gray-700 hover:bg-gray-100 font-bold px-6 py-6 rounded-xl text-lg transition-colors"
        >
          로그아웃
        </Button>

        {/* 회원정보 수정 버튼 (메인 컬러 유지) */}
        <Button
          onClick={() => navigate("/parent/mypage/edit")}
          className="bg-[#5A55D6] hover:bg-[#4844b8] text-white font-bold px-6 py-6 rounded-xl text-lg shadow-md transition-colors"
        >
          회원정보 수정
        </Button>
      </div>
    </header>
  );
}
