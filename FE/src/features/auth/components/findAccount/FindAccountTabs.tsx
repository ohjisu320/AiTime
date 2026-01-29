import { cn } from "@/lib/utils";
import type { FindTabType } from "../../types/findAccount";

interface FindAccountTabsProps {
  activeTab: FindTabType;
  onTabChange: (tab: FindTabType) => void;
}

export default function FindAccountTabs({
  activeTab,
  onTabChange,
}: FindAccountTabsProps) {
  return (
    <div className="flex bg-gray-100 p-1 rounded-xl mb-8">
      <button
        onClick={() => onTabChange("FIND_ID")}
        className={cn(
          "flex-1 py-3 text-sm font-bold rounded-lg transition-all",
          activeTab === "FIND_ID"
            ? "bg-white text-[#5A55D6] shadow-sm"
            : "text-gray-400 hover:text-gray-600",
        )}
      >
        아이디 찾기
      </button>
      <button
        onClick={() => onTabChange("RESET_PW")}
        className={cn(
          "flex-1 py-3 text-sm font-bold rounded-lg transition-all",
          activeTab === "RESET_PW"
            ? "bg-white text-[#5A55D6] shadow-sm"
            : "text-gray-400 hover:text-gray-600",
        )}
      >
        비밀번호 재설정
      </button>
    </div>
  );
}
