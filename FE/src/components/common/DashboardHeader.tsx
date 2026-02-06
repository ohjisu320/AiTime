// ✨ [수정] import type으로 변경
import type { ReactNode } from "react";

export interface DashboardTab {
  value: string;
  label: string;
  count?: number;
}

interface DashboardHeaderProps {
  title: string;
  description: string;
  tabs: DashboardTab[];
  activeTab: string;
  onTabChange: (value: string) => void;
  children?: ReactNode;
}

export default function DashboardHeader({
  title,
  description,
  tabs,
  activeTab,
  onTabChange,
  children,
}: DashboardHeaderProps) {
  return (
    <header className="px-10 pt-10 pb-0 bg-white border-b border-gray-200">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-2xl font-bold text-[#1A1A1A]">{title}</h1>
        {children}
      </div>

      <p className="text-gray-500 text-sm mb-8">{description}</p>

      <div className="flex gap-8">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => onTabChange(tab.value)}
            className={`pb-3 text-sm font-bold transition-all border-b-2 ${
              activeTab === tab.value
                ? "text-[#5A55D6] border-[#5A55D6]"
                : "text-gray-400 border-transparent hover:text-gray-600"
            }`}
          >
            {tab.label} {tab.count !== undefined && `(${tab.count})`}
          </button>
        ))}
      </div>
    </header>
  );
}
