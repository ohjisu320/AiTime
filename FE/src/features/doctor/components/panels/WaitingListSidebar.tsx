import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { doctorApi } from "../../api/doctorApi";
import type { PatientDto } from "../../types/doctor";
import LogoutModal from "../modals/LogoutModal";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectPatient: (patient: PatientDto) => void;
}

export default function WaitingListSidebar({
  onSelectPatient,
}: Omit<Props, "isOpen" | "onClose">) {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  const [reservedDates, setReservedDates] = useState<string[]>([]);
  const [patients, setPatients] = useState<PatientDto[]>([]);
  const [isCalendarLoading, setIsCalendarLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isLogoutModalOpen, setLogoutModalOpen] = useState(false);

  const doctorInfo = useMemo(() => {
    try {
      const userStr = localStorage.getItem("user");
      const user = userStr ? JSON.parse(userStr) : null;
      return {
        name: user?.name || "알 수 없음",
        department: "소아청소년과"
      };
    } catch {
      return { name: "알 수 없음", department: "정보 없음" };
    }
  }, []);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleString("ko-KR", {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", hour12: false,
      }).replace(/\./g, "-").replace(" ", " "));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000 * 60);
    return () => clearInterval(timer);
  }, []);

  const formatDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const fetchCalendarData = useCallback(async () => {
    setIsCalendarLoading(true);
    try {
      const year = currentMonth.getFullYear();
      const month = currentMonth.getMonth() + 1;
      const dates = await doctorApi.getReservationCalendar(year, month);
      setReservedDates(dates || []);
    } catch (error) {
      console.error("캘린더 로드 실패:", error);
    } finally {
      setIsCalendarLoading(false);
    }
  }, [currentMonth]);

  const fetchPatients = useCallback(async () => {
    setIsLoading(true);
    try {
      const dateStr = formatDate(selectedDate);
      const response = await doctorApi.searchPatients({
        page: 0,
        size: 100,
        date: dateStr,
        year: selectedDate.getFullYear(),
        month: selectedDate.getMonth() + 1,
        day: selectedDate.getDate(),
      });
      if (response?.code === 200 && response.data?.data) {
        setPatients(response.data.data);
      } else {
        setPatients([]);
      }
    } catch (error) {
      console.error("환자 목록 로드 실패:", error);
      setPatients([]);
    } finally {
      setIsLoading(false);
    }
  }, [selectedDate]);

  // [수정] isOpen 의존성 제거 - 항상 마운트 시 데이터 로드
  useEffect(() => {
    fetchCalendarData();
    fetchPatients();
  }, [fetchCalendarData, fetchPatients]);

  const changeMonth = (delta: number) => {
    setCurrentMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + delta, 1));
  };

  const handleDayClick = (day: number) => {
    const newDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    setSelectedDate(newDate);
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    return { daysInMonth: lastDay.getDate(), startDayOfWeek: firstDay.getDay() };
  };

  const { daysInMonth, startDayOfWeek } = getDaysInMonth(currentMonth);
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  // [Added] Logout handler
  const handleLogoutClick = () => {
    setLogoutModalOpen(true);
  };

  const handleConfirmLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <div className="h-full w-full bg-[#d4d0c8] font-['Gulim'] text-[13px] flex flex-col overflow-hidden">
      <div className="flex-1 flex flex-col p-[4px] gap-2 overflow-hidden">

        <div className="bg-white border-2 border-[#808080] border-r-white border-b-white p-[8px]">
          <div className="font-bold text-[#000080] mb-[4px] border-b border-gray-200 pb-1">[담당의 정보]</div>
          <div className="leading-snug">성명: {doctorInfo.name}</div>
          <div className="leading-snug">소속: {doctorInfo.department}</div>
        </div>

        <div className="bg-white border-2 border-[#808080] border-r-white border-b-white relative min-h-[220px]">
          {isCalendarLoading && (
            <div className="absolute inset-0 z-10 bg-white/80 flex items-center justify-center">
              <span className="text-blue-800 font-bold animate-pulse">Loading...</span>
            </div>
          )}

          <div className="bg-[#000080] text-white p-[4px] flex items-center justify-between mb-1">
            <button onClick={() => changeMonth(-1)} className="w-[24px] bg-[#d4d0c8] text-black text-[12px] border border-white border-r-[#404040] border-b-[#404040] active:border-inset hover:bg-gray-200">◀</button>
            <span className="font-bold text-[13px]">{currentMonth.getFullYear()}년 {currentMonth.getMonth() + 1}월</span>
            <button onClick={() => changeMonth(1)} className="w-[24px] bg-[#d4d0c8] text-black text-[12px] border border-white border-r-[#404040] border-b-[#404040] active:border-inset hover:bg-gray-200">▶</button>
          </div>

          <div className="grid grid-cols-7 border-b border-[#ececec] mb-1">
            {weekDays.map((day, i) => (
              <div key={day} className={cn(
                "text-center py-[2px] font-bold text-[12px]",
                i === 0 && "text-red-600",
                i === 6 && "text-blue-600"
              )}>{day}</div>
            ))}
          </div>

          <div className="grid grid-cols-7">
            {Array.from({ length: startDayOfWeek }).map((_, i) => (
              <div key={`empty-${i}`} className="h-[28px]" />
            ))}

            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const dayOfWeek = (startDayOfWeek + i) % 7;
              const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
              // [수정] 평일(월~금)은 무조건 예약된 것으로 간주 (0: 일요일, 6: 토요일)
              const isReserved = reservedDates.includes(dateStr) || (dayOfWeek !== 0 && dayOfWeek !== 6);
              const isSelected = selectedDate.getDate() === day && selectedDate.getMonth() === currentMonth.getMonth();
              const isToday = new Date().getDate() === day && new Date().getMonth() === currentMonth.getMonth();

              return (
                <div
                  key={`day-${day}`}
                  onClick={() => handleDayClick(day)}
                  className={cn(
                    "h-[28px] flex items-center justify-center cursor-pointer text-[12px] relative border border-transparent",
                    dayOfWeek === 0 && "text-red-600",
                    dayOfWeek === 6 && "text-blue-600",
                    isSelected && "bg-[#000080] text-white hover:bg-[#000080] hover:text-white",
                    !isSelected && isToday && "bg-[#ffffcc] font-bold ring-1 ring-inset ring-orange-300",
                    !isSelected && !isToday && "hover:bg-[#d4d0c8] hover:border-[#808080]"
                  )}
                >
                  {day}
                  {isReserved && !isSelected && (
                    <span className="absolute bottom-[3px] w-[5px] h-[5px] bg-red-500 rounded-full" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex-1 flex flex-col min-h-0 bg-white border-2 border-[#808080] border-r-white border-b-white">
          <div className="bg-[#000080] text-white px-2 py-1 font-bold shrink-0 text-[13px]">
            ▣ {formatDate(selectedDate)} 예약 환자
          </div>

          <div className="flex-1 overflow-y-auto p-1">
            {isLoading ? (
              <div className="p-4 text-center text-gray-500">목록 로딩 중...</div>
            ) : patients.length === 0 ? (
              <div className="p-4 text-center text-gray-500 text-[12px]">
                예약된 환자가 없습니다.
              </div>
            ) : (
              patients.map((patient, index) => (
                <div
                  key={patient.childId}
                  onClick={() => { onSelectPatient(patient); }}
                  className="group flex justify-between items-center p-2 border-b border-[#ececec] cursor-pointer hover:bg-[#000080] hover:text-white transition-colors"
                >
                  <div className="truncate font-bold text-[13px]">
                    {index + 1}. {patient.childName}
                  </div>
                  <div className="text-[12px] text-gray-500 group-hover:text-gray-200">
                    ({patient.gender === "MALE" ? "남" : "여"}/{patient.months}m)
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* [Added] Logout Button */}
        <div className="p-[4px] pb-0">
          <button
            onClick={handleLogoutClick}
            className="w-full bg-[#d4d0c8] border border-white border-r-[#404040] border-b-[#404040] py-1 text-[12px] active:border-t-[#404040] active:border-l-[#404040] active:border-r-white active:border-b-white active:translate-y-[1px] hover:bg-[#e0e0e0] font-bold text-red-700"
          >
            로그아웃
          </button>
        </div>

        <div className="bg-black border border-white/30 p-[4px] text-right text-[#00ff00] shrink-0 text-[14px] font-mono tracking-wider shadow-inner">
          <span className="text-[11px] text-[#00ff00]/70 mr-2 font-sans tracking-normal">CURRENT TIME</span>
          {currentTime}
        </div>

      </div>

      {isLogoutModalOpen && (
        <LogoutModal
          onConfirm={handleConfirmLogout}
          onCancel={() => setLogoutModalOpen(false)}
        />
      )}
    </div>
  );
}