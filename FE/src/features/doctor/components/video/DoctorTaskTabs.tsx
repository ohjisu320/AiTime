import { TASK_TABS, type VideoType } from "./doctor-video-data";

interface DoctorTaskTabsProps {
  activeTask: VideoType;
  onTaskChange: (task: VideoType) => void;
}

export default function DoctorTaskTabs({
  activeTask,
  onTaskChange,
}: DoctorTaskTabsProps) {
  return (
    // [수정] 높이 h-20 -> h-28
    <div className="h-28 bg-white border-b border-gray-200 flex items-center justify-center px-6 flex-shrink-0 z-10 shadow-sm">
      <div className="flex gap-3 p-1.5 bg-gray-100 rounded-2xl overflow-x-auto no-scrollbar">
        {TASK_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTaskChange(tab.id)}
            // [수정] 패딩, 폰트 사이즈 대폭 확대
            className={`px-10 py-4 rounded-xl text-lg font-bold transition-all whitespace-nowrap
              ${
                activeTask === tab.id
                  ? "bg-white text-[#5A55D6] shadow-md ring-1 ring-black/5"
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}
