import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, ChevronLeft, ChevronRight, User } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AppSidebarProps {
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
  markedDates: string[]; // 달력에 점을 표시할 날짜 배열
  onMonthChange?: (year: number, month: number) => void;
  userInfo: {
    name: string;
    roleLabel: string; // 예: "소아청소년과 전문의"
    systemLabel: string; // 예: "의사용 시스템"
  };
}

export default function AppSidebar({
  selectedDate,
  onDateSelect,
  markedDates,
  onMonthChange,
  userInfo,
}: AppSidebarProps) {
  const navigate = useNavigate();
  const [viewDate, setViewDate] = useState(new Date());

  useEffect(() => {
    setViewDate(selectedDate);
    // 초기 마운트 시에도 캘린더 데이터가 필요할 수 있으므로, 초기값으로 onMonthChange 호출 고려?
    // 하지만 Dashboard에서 초기 호출 하는 게 나음.
  }, [selectedDate]);

  useEffect(() => {
    onMonthChange?.(viewDate.getFullYear(), viewDate.getMonth() + 1);
  }, [viewDate, onMonthChange]);

  const handleLogout = () => {
    // 로그아웃 로직 (토큰 삭제 등) 수행 후 이동
    navigate("/login");
  };

  const handleMonthChange = (direction: -1 | 1) => {
    const newDate = new Date(viewDate.getFullYear(), viewDate.getMonth() + direction, 1);
    setViewDate(newDate);
    onMonthChange?.(newDate.getFullYear(), newDate.getMonth() + 1);
  };

  const handlePrevMonth = () => handleMonthChange(-1);
  const handleNextMonth = () => handleMonthChange(1);

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfWeek = new Date(year, month, 1).getDay();

  const getFormattedDate = (d: number) => {
    const m = String(month + 1).padStart(2, "0");
    const dayStr = String(d).padStart(2, "0");
    return `${year}-${m}-${dayStr}`;
  };

  const isSameDay = (d1: Date, d2: Date) => {
    return (
      d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate()
    );
  };

  return (
    <aside className="w-[280px] h-screen bg-white border-r border-gray-200 flex flex-col flex-none sticky top-0 z-50">
      {/* 로고 영역 */}
      <div className="h-16 flex items-center px-6 border-b border-gray-100">
        <div className="w-8 h-8 bg-[#5A55D6] rounded-lg flex items-center justify-center text-white font-bold text-xs mr-2">
          Ai
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-bold text-[#1A1A1A] leading-none">
            AiTime
          </span>
          <span className="text-[10px] text-gray-500 mt-1">
            {userInfo.systemLabel}
          </span>
        </div>
      </div>

      {/* 프로필 카드 */}
      <div className="p-6">
        <div className="bg-[#F5F7FF] rounded-2xl p-5 flex items-center gap-4">
          <div className="w-12 h-12 bg-[#5A55D6] rounded-full flex items-center justify-center text-white shrink-0">
            <User className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <div className="font-bold text-[#1A1A1A] truncate">
              {userInfo.name}
            </div>
            <div className="text-xs text-gray-500 truncate">
              {userInfo.roleLabel}
            </div>
          </div>
        </div>
      </div>

      {/* 달력 */}
      <div className="px-6 flex-1 overflow-y-auto">
        <div className="mb-4 flex items-center justify-between">
          <span className="font-bold text-gray-800">
            {year}년 {month + 1}월
          </span>
          <div className="flex gap-1">
            <button
              onClick={handlePrevMonth}
              className="p-1 hover:bg-gray-100 rounded text-gray-500"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={handleNextMonth}
              className="p-1 hover:bg-gray-100 rounded text-gray-500"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="grid grid-cols-7 text-center text-xs gap-y-4 text-gray-500 font-['Inter']">
          {["일", "월", "화", "수", "목", "금", "토"].map((day) => (
            <div key={day} className="font-medium text-gray-400">
              {day}
            </div>
          ))}
          {Array.from({ length: firstDayOfWeek }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}
          {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
            const dateStr = getFormattedDate(day);
            const currentDayObj = new Date(year, month, day);
            const hasMark = markedDates.includes(dateStr);
            const isSelected = isSameDay(currentDayObj, selectedDate);
            return (
              <div
                key={day}
                onClick={() => onDateSelect(currentDayObj)}
                className="flex flex-col items-center justify-center gap-1 cursor-pointer group relative"
              >
                <div
                  className={`w-8 h-8 flex items-center justify-center rounded-full transition-all ${isSelected ? "bg-[#5A55D6] text-white font-bold shadow-md" : "group-hover:bg-gray-100 text-gray-700"}`}
                >
                  {day}
                </div>
                {hasMark && !isSelected && (
                  <div className="absolute -bottom-1 w-1 h-1 bg-[#5A55D6] rounded-full" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 로그아웃 */}
      <div className="p-6 border-t border-gray-100">
        <Button
          variant="ghost"
          onClick={handleLogout}
          className="w-full flex justify-start gap-2 text-gray-500 hover:text-red-500 hover:bg-red-50"
        >
          <LogOut className="w-5 h-5" /> 로그아웃
        </Button>
      </div>
    </aside>
  );
}
