import { X } from "lucide-react";

export interface ChildProfile {
  childId: string;
  name: string;
  months: number;
  gender: "MALE" | "FEMALE";
  birthdate: string;
}

interface ProfileCardProps {
  profile: ChildProfile;
  isManageMode: boolean;
  onClick: (profile: ChildProfile) => void;
  onDelete: (profile: ChildProfile) => void;
}

export default function ProfileCard({
  profile,
  isManageMode,
  onClick,
  onDelete,
}: ProfileCardProps) {
  return (
    <div className="relative group">
      {/* 삭제 버튼 (크기 증가) */}
      {isManageMode && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(profile);
          }}
          className="absolute 0 top-0 -right-2 z-10 w-10 h-10 bg-gray-400 text-white rounded-full flex items-center justify-center hover:bg-red-500 transition-colors shadow-md"
        >
          <X className="w-6 h-6" />
        </button>
      )}

      <div
        onClick={() => onClick(profile)}
        className={`flex flex-col items-center gap-5 cursor-pointer ${
          isManageMode ? "pointer-events-none" : ""
        }`}
      >
        {/* 아바타 (크기 대폭 증가 w-48) */}
        <div
          className={`w-40 h-40 md:w-48 md:h-48 rounded-full relative flex items-center justify-center shadow-xl transform transition-transform group-hover:scale-105 ring-8 ring-white ${
            profile.gender === "MALE" ? "bg-blue-200" : "bg-pink-200"
          }`}
        >
          <span className="text-7xl md:text-8xl drop-shadow-md">
            {profile.gender === "MALE" ? "👦" : "👧"}
          </span>
        </div>

        {/* 정보 (폰트 증가) */}
        <div className="text-center space-y-1">
          <div className="text-2xl md:text-3xl font-bold text-gray-800">
            {profile.name}
          </div>
          <div className="text-base md:text-lg text-gray-500 font-medium">
            {profile.months}개월
          </div>
        </div>
      </div>
    </div>
  );
}
