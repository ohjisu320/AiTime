// src/features/auth/components/LoginTabs.tsx
import { cn } from "@/lib/utils";

interface LoginTabsProps {
  activeTab: "PARENT";
  onTabChange: (tab: "PARENT") => void;
}

export default function LoginTabs({ activeTab, onTabChange }: LoginTabsProps) {
  return (
    <div className="flex justify-end mb-6">
      <div className="flex gap-2 bg-transparent">
        <TabButton
          label="부모"
          isActive={activeTab === "PARENT"}
          onClick={() => onTabChange("PARENT")}
        />
      </div>
    </div>
  );
}

// 내부용 탭 버튼 (스타일 분리)
const TabButton = ({
  label,
  isActive,
  onClick,
}: {
  label: string;
  isActive: boolean;
  onClick: () => void;
}) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "w-[120px] py-3 rounded-2xl text-lg font-bold transition-all duration-300",
      isActive
        ? "bg-[#9593D9] text-white shadow-md"
        : "bg-[#F3F4F6] text-slate-400 hover:bg-slate-200",
    )}
  >
    {label}
  </button>
);
