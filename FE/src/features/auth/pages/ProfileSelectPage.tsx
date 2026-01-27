import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

import ProfileHeader from "../components/ProfileHeader";
import ProfileCard, { type ChildProfile } from "../components/ProfileCard";
import AddProfileButton from "../components/AddProfileButton";
import AddProfileModal, {
  type AddProfileFormData,
} from "../components/AddProfileModal";
import DeleteProfileModal from "../components/DeleteProfileModal";

export default function ProfileSelectPage() {
  const navigate = useNavigate();

  // --- State ---
  const [profiles, setProfiles] = useState<ChildProfile[]>([
    {
      childId: "uuid-1",
      name: "민준",
      months: 18,
      gender: "MALE",
      birthdate: "2024-08-01",
    },
    {
      childId: "uuid-2",
      name: "서아",
      months: 22,
      gender: "FEMALE",
      birthdate: "2024-04-01",
    },
    {
      childId: "uuid-3",
      name: "도윤",
      months: 15,
      gender: "MALE",
      birthdate: "2024-11-01",
    },
  ]);

  const [isManageMode, setIsManageMode] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ChildProfile | null>(null);

  // --- Logic ---
  const calculateMonths = (dateStr: string) => {
    const birth = new Date(dateStr.replace(/\./g, "-"));
    const now = new Date();
    const months =
      (now.getFullYear() - birth.getFullYear()) * 12 +
      (now.getMonth() - birth.getMonth());
    return months > 0 ? months : 0;
  };

  const handleProfileClick = (profile: ChildProfile) => {
    console.log("Selected Child:", profile.childId);
    navigate("/parent/dashboard");
  };

  const handleAddProfile = (data: AddProfileFormData) => {
    const newProfile: ChildProfile = {
      childId: `uuid-${Date.now()}`,
      name: data.name,
      birthdate: data.birthdate,
      months: calculateMonths(data.birthdate),
      gender: data.gender as "MALE" | "FEMALE",
    };
    setProfiles([...profiles, newProfile]);
    setIsAddModalOpen(false);
  };

  const handleConfirmDelete = () => {
    if (!deleteTarget) return;
    setProfiles(profiles.filter((p) => p.childId !== deleteTarget.childId));
    setDeleteTarget(null);
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#f9f8fc] via-[#E6E6FA] to-[#d1c7ee] relative flex flex-col font-['Pretendard']">
      {/* 1. 헤더 */}
      <ProfileHeader />

      {/* 2. 메인 컨텐츠 */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 -mt-10 animate-fade-in">
        <div className="text-center mb-16 space-y-4">
          {/* 타이틀 크기 증가 */}
          <h1 className="text-3xl md:text-5xl font-bold text-gray-800 tracking-tight">
            {isManageMode
              ? "어떤 아이의 정보를 수정하나요?"
              : "누가 검사를 진행하나요?"}
          </h1>
          {/* 서브텍스트 크기 증가 */}
          <p className="text-gray-500 text-lg md:text-xl">
            {isManageMode
              ? "지금 수정할 아이를 선택해주세요"
              : "오늘 검사할 아이를 선택해주세요"}
          </p>
        </div>

        {/* 프로필 리스트 & 추가 버튼 (간격 증가) */}
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

        {/* 하단 관리 버튼 (크기 증가) */}
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
