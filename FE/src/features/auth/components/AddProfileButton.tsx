import { Plus } from "lucide-react";

interface AddProfileButtonProps {
  onClick: () => void;
}

export default function AddProfileButton({ onClick }: AddProfileButtonProps) {
  return (
    <div
      onClick={onClick}
      className="flex flex-col items-center gap-5 cursor-pointer group"
    >
      {/* 카드 크기와 동일하게 w-48로 맞춤 */}
      <div className="w-40 h-40 md:w-48 md:h-48 rounded-full bg-white border-4 border-dashed border-gray-300 flex items-center justify-center shadow-sm hover:border-[#9D8AD6] hover:text-[#9D8AD6] transition-all group-hover:scale-105">
        <Plus className="w-16 h-16 text-gray-400 group-hover:text-[#9D8AD6]" />
      </div>
      <div className="text-center opacity-0 group-hover:opacity-100 transition-opacity">
        <span className="text-lg md:text-xl text-[#9D8AD6] font-bold">
          프로필 추가
        </span>
      </div>
    </div>
  );
}
