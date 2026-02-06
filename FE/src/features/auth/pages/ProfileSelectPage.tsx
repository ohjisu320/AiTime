import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

// [UI Components] 기존 디자인 유지
import ProfileHeader from "../components/ProfileHeader";
import ProfileCard, { type ChildProfile } from "../components/ProfileCard";
import AddProfileButton from "../components/AddProfileButton";
import AddProfileModal, {
  type AddProfileFormData,
} from "../components/AddProfileModal";
import DeleteProfileModal from "../components/DeleteProfileModal";

// [API] 실제 API 연결
import {
  getChildren,
  addChild,
  deleteChild,
} from "@/features/auth/api/child/childApi";
import type { ChildCreateRequest } from "@/features/auth/api/child/types";

export default function ProfileSelectPage() {
  const navigate = useNavigate();

  // --- State ---
  const [profiles, setProfiles] = useState<ChildProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true); // 로딩 상태 추가
  const [isManageMode, setIsManageMode] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ChildProfile | null>(null);

  // --- API Functions ---

  // 1. 자녀 목록 불러오기
  const fetchProfiles = async () => {
    try {
      setIsLoading(true);
      const data = await getChildren();

      // API 응답(ChildInfoResponse)을 UI 타입(ChildProfile)으로 변환
      const mappedProfiles: ChildProfile[] = data.map((child) => ({
        childId: child.childId,
        name: child.name,
        months: child.months,
        gender: child.gender,
        birthdate: "", // API 목록 조회에서는 생일이 넘어오지 않지만, UI 표시에 개월수가 우선이라면 공란 처리
      }));

      setProfiles(mappedProfiles);
    } catch (error) {
      console.error("프로필 목록 로드 실패:", error);
      // 필요 시 에러 토스트 메시지 띄우기
    } finally {
      setIsLoading(false);
    }
  };

  // 초기 로딩
  useEffect(() => {
    fetchProfiles();
  }, []);

  // --- Event Handlers ---

  // 2. 프로필 선택 (대시보드 이동)
  const handleProfileClick = (profile: ChildProfile) => {
    localStorage.setItem("selectedChildId", profile.childId);
    console.log("Selected Child:", profile.childId);
    navigate(`/parent/dashboard`); // 라우팅 경로 확인 (기존: /parent/dashboard -> 변경: /child/:id)
  };

  // 3. 프로필 추가 (API 호출)
  const handleAddProfile = async (data: AddProfileFormData) => {
    try {
      // 입력된 생년월일(YYYYMMDD 또는 YYYY.MM.DD)을 YYYY-MM-DD 로 변환
      // 숫자만 남긴 후 하이픈 추가
      const rawDate = data.birthdate.replace(/[^0-9]/g, ""); // "20251223"
      const formattedDate = `${rawDate.slice(0, 4)}-${rawDate.slice(4, 6)}-${rawDate.slice(6, 8)}`; // "2025-12-23"

      const reqData: ChildCreateRequest = {
        name: data.name,
        birthdate: formattedDate, // [수정됨] 변환된 날짜 전송
        gender: data.gender as "MALE" | "FEMALE",
      };

      console.log("전송 데이터 확인:", reqData); // 콘솔에서 확인 가능

      await addChild(reqData); // 서버 전송
      await fetchProfiles(); // 목록 새로고침
      setIsAddModalOpen(false); // 모달 닫기
    } catch (error: any) {
      console.error("자녀 추가 실패:", error);

      // 에러 메시지 사용자에게 알림
      const serverMessage =
        error.response?.data?.message || "입력값을 확인해주세요.";
      alert(`자녀 추가 실패: ${serverMessage}`);
    }
  };
  
  // 4. 프로필 삭제 (API 호출)
  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      await deleteChild(deleteTarget.childId); // 서버 삭제 요청
      await fetchProfiles(); // 목록 새로고침
      setDeleteTarget(null); // 모달 닫기
    } catch (error) {
      console.error("자녀 삭제 실패:", error);
      alert("자녀를 삭제하는데 실패했습니다.");
    }
  };

  // --- Render (기존 스타일 유지) ---

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#f9f8fc] via-[#E6E6FA] to-[#d1c7ee] relative flex flex-col font-['Pretendard']">
      {/* 1. 헤더 */}
      <ProfileHeader />

      {/* 2. 메인 컨텐츠 */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 -mt-10 animate-fade-in">
        <div className="text-center mb-16 space-y-4">
          {/* 타이틀 */}
          <h1 className="text-3xl md:text-5xl font-bold text-gray-800 tracking-tight">
            {isManageMode
              ? "어떤 아이의 정보를 수정하나요?"
              : "누가 검사를 진행하나요?"}
          </h1>
          {/* 서브텍스트 */}
          <p className="text-gray-500 text-lg md:text-xl">
            {isManageMode
              ? "지금 수정할 아이를 선택해주세요"
              : "오늘 검사할 아이를 선택해주세요"}
          </p>
        </div>

        {/* 로딩 상태 처리 (선택사항 - 로딩 중일 때 스켈레톤이나 스피너를 보여줄 수 있음) */}
        {isLoading ? (
          <div className="mb-20 text-gray-500 font-dodam text-xl">
            프로필 불러오는 중...
          </div>
        ) : (
          /* 프로필 리스트 & 추가 버튼 */
          <div className="flex flex-wrap justify-center items-start gap-12 mb-20">
            {profiles.map((profile) => (
              <ProfileCard
                key={profile.childId}
                profile={profile}
                isManageMode={isManageMode}
                onClick={handleProfileClick}
                onDelete={setDeleteTarget}
              />
            ))}
            <AddProfileButton onClick={() => setIsAddModalOpen(true)} />
          </div>
        )}

        {/* 하단 관리 버튼 */}
        <Button
          variant="ghost"
          onClick={() => setIsManageMode(!isManageMode)}
          className={`font-bold px-10 py-8 rounded-full text-xl transition-all shadow-sm hover:scale-105 ${
            isManageMode
              ? "bg-[#5A55D6] text-white hover:bg-[#4844b8]"
              : "bg-purple-50 text-[#9D8AD6] hover:bg-purple-100"
          }`}
        >
          {isManageMode ? "프로필 수정 완료" : "프로필 관리하기"}
        </Button>
      </main>

      {/* ================= MODALS ================= */}
      <AddProfileModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onConfirm={handleAddProfile}
      />

      <DeleteProfileModal
        targetProfile={deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
}
