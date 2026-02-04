import { useState, useEffect, useMemo, useCallback } from "react";
import { cn } from "@/lib/utils";
import { doctorApi } from "../../api/doctorApi";
import type { PatientDto } from "../../types/doctor";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectPatient: (patient: PatientDto) => void;
}

export default function WaitingListSidebar({
  isOpen,
  onClose,
  onSelectPatient,
}: Props) {
  const [currentTime, setCurrentTime] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  const [reservedDates, setReservedDates] = useState<string[]>([]);
  const [patients, setPatients] = useState<PatientDto[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCalendarLoading, setIsCalendarLoading] = useState(false);

  // localStorage에서 로그인한 의사 정보 가져오기
  const doctorInfo = useMemo(() => {
    try {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        const user = JSON.parse(userStr);
        return {
          name: user.name || "알 수 없음",
          department: "소아청소년과"
        };
      }
    } catch (e) {
      console.error("의사 정보 파싱 실패:", e);
    }
    return { name: "알 수 없음", department: "정보 없음" };
  }, []);

  // 실시간 시계 기능
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const formatted = now
        .toLocaleString("ko-KR", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        })
        .replace(/\./g, "-")
        .replace(" ", " ");
      setCurrentTime(formatted);
    };

    updateTime();
    const timer = setInterval(updateTime, 1000 * 60);
    return () => clearInterval(timer);
  }, []);

  // 날짜 포맷 헬퍼
  const formatDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // 월별 캘린더 데이터 로드
  const fetchCalendarData = useCallback(async () => {
    setIsCalendarLoading(true);
    try {
      const year = currentMonth.getFullYear();
      const month = currentMonth.getMonth() + 1;
      const dates = await doctorApi.getReservationCalendar(year, month);
      setReservedDates(dates);
    } catch (error) {
      console.error("캘린더 데이터 로드 실패:", error);
      setReservedDates([]);
    } finally {
      setIsCalendarLoading(false);
    }
  }, [currentMonth]);

  // 선택 날짜 환자 목록 로드
  const fetchPatients = useCallback(async () => {
    setIsLoading(true);
    try {
      const dateStr = formatDate(selectedDate);
      const response = await doctorApi.searchPatients({
        page: 0,
        size: 100,
        date: dateStr,
      });
      if (response.code === 200 && response.data?.childResponses) {
        setPatients(response.data.childResponses);
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

  // 월 변경 시 캘린더 데이터 로드
  useEffect(() => {
    if (isOpen) {
      fetchCalendarData();
    }
  }, [isOpen, fetchCalendarData]);

  // 날짜 변경 시 환자 목록 로드
  useEffect(() => {
    if (isOpen) {
      fetchPatients();
    }
  }, [isOpen, selectedDate, fetchPatients]);

  // 환자 클릭 핸들러
  const handlePatientClick = (patient: PatientDto) => {
    onSelectPatient(patient);
    onClose();
  };

  // 달력 헬퍼 함수들
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startDayOfWeek = firstDay.getDay();
    return { daysInMonth, startDayOfWeek };
  };

  const isReservedDate = (day: number) => {
    const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return reservedDates.includes(dateStr);
  };

  const isSelectedDate = (day: number) => {
    return (
      selectedDate.getFullYear() === currentMonth.getFullYear() &&
      selectedDate.getMonth() === currentMonth.getMonth() &&
      selectedDate.getDate() === day
    );
  };

  const isToday = (day: number) => {
    const today = new Date();
    return (
      today.getFullYear() === currentMonth.getFullYear() &&
      today.getMonth() === currentMonth.getMonth() &&
      today.getDate() === day
    );
  };

  const handleDayClick = (day: number) => {
    const newDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    setSelectedDate(newDate);
  };

  const changeMonth = (delta: number) => {
    setCurrentMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + delta, 1));
  };

  const { daysInMonth, startDayOfWeek } = getDaysInMonth(currentMonth);
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  if (!isOpen) return null;

  return (
    <>
      {/* 배경 오버레이 */}
      <div className="fixed inset-0 bg-black/50 z-[1500]" onClick={onClose} />

      {/* 사이드바 본체 */}
      <div
        className={cn(
          "fixed left-0 top-0 h-full w-[320px] bg-[#d4d0c8] border-r-2 border-white z-[2000] transition-transform font-['Gulim'] text-[11px]",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* 1. 타이틀 바 */}
          <div className="bg-[#000080] p-[4px] flex items-center justify-between text-white shrink-0">
            <span className="font-bold">▣ 환자 예약 관리</span>
            <button
              onClick={onClose}
              className="w-[18px] h-[18px] bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] text-black text-[11px] leading-none flex items-center justify-center cursor-pointer"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 flex flex-col p-[10px] overflow-hidden">
            {/* 2. 의사 정보 */}
            <div className="bg-white border-2 border-[#808080] border-r-white border-b-white p-[8px] mb-[10px]">
              <div className="font-bold text-[#000080] mb-[3px]">
                [담당의 정보]
              </div>
              <div>성명: {doctorInfo.name} 전문의</div>
              <div>소속: {doctorInfo.department}</div>
            </div>

            {/* 3. Windows 98 스타일 달력 */}
            <div className="bg-white border-2 border-[#808080] border-r-white border-b-white mb-[10px] shrink-0">
              {/* 달력 헤더 */}
              <div className="bg-[#000080] text-white p-[4px] flex items-center justify-between">
                <button
                  onClick={() => changeMonth(-1)}
                  className="w-[20px] h-[16px] bg-[#d4d0c8] border border-white border-r-[#404040] border-b-[#404040] text-black text-[10px] flex items-center justify-center"
                >
                  ◀
                </button>
                <span className="font-bold">
                  {currentMonth.getFullYear()}년 {currentMonth.getMonth() + 1}월
                </span>
                <button
                  onClick={() => changeMonth(1)}
                  className="w-[20px] h-[16px] bg-[#d4d0c8] border border-white border-r-[#404040] border-b-[#404040] text-black text-[10px] flex items-center justify-center"
                >
                  ▶
                </button>
              </div>

              {/* 요일 헤더 */}
              <div className="grid grid-cols-7 border-b border-[#808080]">
                {weekDays.map((day, i) => (
                  <div
                    key={day}
                    className={cn(
                      "text-center py-[2px] font-bold text-[10px]",
                      i === 0 && "text-red-600",
                      i === 6 && "text-blue-600"
                    )}
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* 달력 본체 */}
              <div className="grid grid-cols-7">
                {/* 빈 칸 */}
                {Array.from({ length: startDayOfWeek }).map((_, i) => (
                  <div key={`empty-${i}`} className="h-[24px]" />
                ))}
                {/* 날짜 칸 */}
                {Array.from({ length: daysInMonth }).map((_, i) => {
                  const day = i + 1;
                  const dayOfWeek = (startDayOfWeek + i) % 7;
                  const reserved = isReservedDate(day);
                  const selected = isSelectedDate(day);
                  const today = isToday(day);

                  return (
                    <div
                      key={day}
                      onClick={() => handleDayClick(day)}
                      className={cn(
                        "h-[24px] flex items-center justify-center cursor-pointer text-[10px] relative",
                        dayOfWeek === 0 && "text-red-600",
                        dayOfWeek === 6 && "text-blue-600",
                        selected && "bg-[#000080] text-white",
                        !selected && today && "bg-[#ffffcc]",
                        !selected && "hover:bg-[#d4d0c8]"
                      )}
                    >
                      {day}
                      {reserved && !selected && (
                        <span className="absolute bottom-[2px] w-[4px] h-[4px] bg-red-500 rounded-full" />
                      )}
                    </div>
                  );
                })}
              </div>

              {isCalendarLoading && (
                <div className="text-center py-[2px] text-[9px] text-gray-500">로딩 중...</div>
              )}
            </div>

            {/* 4. 선택된 날짜의 환자 목록 */}
            <div className="flex-1 flex flex-col min-h-0">
              <div className="font-bold mb-[5px]">
                ▣ {formatDate(selectedDate)} 예약 환자
              </div>

              <div className="flex-1 bg-white border-2 border-[#808080] border-r-white border-b-white overflow-y-auto mb-[10px]">
                {isLoading ? (
                  <div className="p-[5px] text-center text-gray-500">로딩 중...</div>
                ) : patients.length === 0 ? (
                  <div className="p-[5px] text-center text-gray-500">예약 환자 없음</div>
                ) : (
                  patients.map((patient, index) => (
                    <div
                      key={patient.childId}
                      onClick={() => handlePatientClick(patient)}
                      className="p-[5px] border-b border-[#ececec] cursor-pointer hover:bg-[#000080] hover:text-white select-none truncate"
                    >
                      {String(index + 1).padStart(2, "0")}. {patient.name} (
                      {patient.gender === "MALE" ? "남" : "여"}/{Math.floor(patient.monthlyAge / 12)}세)
                    </div>
                  ))
                )}
              </div>

              {/* 5. 현재 시각 */}
              <div className="bg-white border-2 border-[#808080] border-r-white border-b-white p-[5px] text-center shrink-0">
                현재 시각: {currentTime}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
