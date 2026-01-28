import { ArrowLeft, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { TaskVideoItem } from "./doctor-video-data";

interface DoctorTaskSidebarProps {
  videoList: TaskVideoItem[];
  currentIndex: number;
  onDateClick: (index: number) => void;
  onBack: () => void;
}

export default function DoctorTaskSidebar({
  videoList,
  currentIndex,
  onDateClick,
  onBack,
}: DoctorTaskSidebarProps) {
  return (
    // [수정] 너비 280px -> 380px 로 확대
    <aside className="w-[380px] bg-white border-r border-gray-200 flex flex-col flex-shrink-0 z-20">
      {/* Header: 높이 h-20 -> h-24 */}
      <div className="h-24 flex items-center px-8 border-b border-gray-100">
        <Button
          variant="ghost"
          onClick={onBack}
          className="p-0 hover:bg-transparent text-gray-500 hover:text-gray-900 gap-3 font-bold text-xl"
        >
          <ArrowLeft className="w-7 h-7" />
          돌아가기
        </Button>
      </div>

      {/* Patient Info: 패딩 및 폰트 사이즈 확대 */}
      <div className="p-8 border-b border-gray-100 bg-[#F8F9FC]">
        <div className="flex items-center gap-5">
          {/* 아바타 크기 확대 */}
          <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center border border-gray-200 shadow-sm text-3xl">
            👶
          </div>
          <div>
            <div className="font-bold text-gray-900 text-2xl mb-1">박지우</div>
            <div className="text-base text-gray-500 font-medium">
              15개월 | 남아
            </div>
          </div>
        </div>
      </div>

      {/* Date List: 버튼 크기 및 폰트 확대 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar">
        <p className="text-sm font-bold text-gray-400 px-2 mb-3 uppercase tracking-wider">
          Exam History
        </p>
        {videoList.map((item, index) => {
          const isActive = index === currentIndex;
          return (
            <button
              key={item.videoId}
              onClick={() => onDateClick(index)}
              // [수정] py-3 -> py-5, text-sm -> text-lg (버튼 대형화)
              className={`w-full flex items-center justify-between px-6 py-5 rounded-2xl transition-all text-lg font-bold
                ${
                  isActive
                    ? "bg-[#5A55D6] text-white shadow-lg shadow-indigo-200 transform scale-[1.02]"
                    : "text-gray-500 hover:bg-gray-100 hover:text-gray-900"
                }`}
            >
              <div className="flex items-center gap-4">
                <Calendar
                  className={`w-6 h-6 ${isActive ? "text-white" : "text-gray-400"}`}
                />
                {item.examDate}
              </div>
              {isActive && (
                <div className="w-2.5 h-2.5 bg-white rounded-full animate-pulse" />
              )}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
