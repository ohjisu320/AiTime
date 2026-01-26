import { useNavigate } from "react-router-dom";
import { Plus } from "lucide-react"; // Settings 아이콘 제거
import { Button } from "@/components/ui/button";

// 데이터 타입 정의 (API 명세서: ChildListResponse > ChildDto 준수)
interface ChildProfile {
  childId: string; // UUID (기존 id -> childId)
  name: string;
  months: number; // 개월 수 (기존 birthDate -> months)
  gender: "MALE" | "FEMALE"; // 성별 (기존 "boy"|"girl" -> "MALE"|"FEMALE")
}

export default function ProfileSelectPage() {
  const navigate = useNavigate();

  // ✅ UI 확인용 임시 데이터 (API 응답 예시 구조 반영)
  const profiles: ChildProfile[] = [
    { childId: "uuid-1", name: "민준", months: 18, gender: "MALE" },
    { childId: "uuid-2", name: "서아", months: 22, gender: "FEMALE" },
    { childId: "uuid-3", name: "도윤", months: 15, gender: "MALE" },
  ];

  // --- 단순 페이지 이동 핸들러 ---
  const handleProfileClick = () => {
    navigate("/parent/dashboard");
  };

  const handleEditProfile = () => {
    // 회원정보 수정 페이지로 이동 
    navigate("/parent/mypage/edit");
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#f9f8fc] via-[#E6E6FA] to-[#d1c7ee] relative flex flex-col">
      
      {/* 1. 헤더 */}
      <header className="w-full px-6 py-6 flex justify-between items-center">
        {/* 로고 영역 */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-b from-[#9D8AD6] to-violet-500 rounded-lg flex items-center justify-center text-white font-bold text-xs">
            Ai
          </div>
          <span className="text-xl font-bold text-gray-800 font-['Arial']">
            AiTime
          </span>
        </div>

        {/* ✨ 회원정보 수정 버튼 (디자인 반영) */}
        <Button 
          onClick={handleEditProfile}
          className="bg-[#5A55D6] hover:bg-[#4844b8] text-white font-bold px-4 py-2 rounded-lg text-sm shadow-md transition-colors"
        >
          회원정보 수정
        </Button>
      </header>

      {/* 2. 메인 컨텐츠 */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 -mt-10 animate-fade-in">
        {/* 타이틀 */}
        <div className="text-center mb-12 space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800">
            누가 검사를 진행하나요?
          </h1>
          <p className="text-gray-500 text-sm md:text-base">
            오늘 검사할 아이를 선택해주세요
          </p>
        </div>

        {/* 프로필 리스트 영역 */}
        <div className="flex flex-wrap justify-center items-start gap-8 mb-16">
          {/* 반복 렌더링: 아이 프로필 */}
          {profiles.map((profile) => (
            <div
              key={profile.childId}
              onClick={handleProfileClick}
              className="flex flex-col items-center gap-3 cursor-pointer group"
            >
              {/* 아바타 */}
              <div
                className={`w-24 h-24 md:w-28 md:h-28 rounded-full relative flex items-center justify-center shadow-lg transform transition-transform group-hover:scale-105 ring-4 ring-white ${profile.gender === "MALE" ? "bg-blue-200" : "bg-pink-200"}`}
              >
                <span className="text-5xl md:text-6xl drop-shadow-md">
                  {profile.gender === "MALE" ? "👦" : "👧"}
                </span>
              </div>

              {/* 정보 */}
              <div className="text-center">
                <div className="text-xl font-bold text-gray-800">
                  {profile.name}
                </div>
                <div className="text-xs text-gray-500 font-medium">
                  {profile.months}개월
                </div>
              </div>
            </div>
          ))}

          {/* 추가 버튼 (기능 없음, UI만 존재) */}
          <div className="flex flex-col items-center gap-3 cursor-pointer group">
            <div className="w-24 h-24 md:w-28 md:h-28 rounded-full bg-white border-2 border-dashed border-gray-300 flex items-center justify-center shadow-sm hover:border-[#9D8AD6] hover:text-[#9D8AD6] transition-all group-hover:scale-105">
              <Plus className="w-8 h-8 text-gray-400 group-hover:text-[#9D8AD6]" />
            </div>
            <div className="text-center opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-xs text-[#9D8AD6] font-bold">
                프로필 추가
              </span>
            </div>
          </div>
        </div>

        {/* 3. 하단 관리 버튼 */}
        <Button
          variant="ghost"
          className="bg-purple-50 hover:bg-purple-100 text-[#9D8AD6] font-bold px-6 py-6 rounded-full text-base"
        >
          프로필 관리하기
        </Button>
      </main>
    </div>
  );
}