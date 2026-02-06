// src/features/doctor/components/panels/WaitingListSidebar.tsx
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
  // --- State ---
  const [currentTime, setCurrentTime] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());

  const [reservedDates, setReservedDates] = useState<string[]>([]);
  const [patients, setPatients] = useState<PatientDto[]>([]);

  // 로딩 상태
  const [isCalendarLoading, setIsCalendarLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // --- 의사 정보 (LocalStorage) ---
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

  // --- 시계 (1분 단위 갱신) ---
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

  // --- 날짜 포맷 (YYYY-MM-DD) ---
  const formatDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // --- 1. 캘린더 데이터 로드 (월별 예약 현황) ---
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

  // --- 2. 환자 목록 로드 (선택된 날짜) ---
  const fetchPatients = useCallback(async () => {
    setIsLoading(true);
    try {
      const dateStr = formatDate(selectedDate);

      // [수정] year, month, day 파라미터 추가 전송 (백엔드 필터링 지원)
      const response = await doctorApi.searchPatients({
        page: 0,
        size: 100,
        date: dateStr,
        year: selectedDate.getFullYear(),
        month: selectedDate.getMonth() + 1,
        day: selectedDate.getDate(),
      });

      // [수정] 응답 구조 대응: response.data.data (로그 기반 수정)
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

  // --- Effects ---
  useEffect(() => {
    if (isOpen) {
      fetchCalendarData();
      fetchPatients();
    }
  }, [isOpen, fetchCalendarData, fetchPatients]);

  // --- Handlers ---
  const changeMonth = (delta: number) => {
    setCurrentMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + delta, 1));
  };

  const handleDayClick = (day: number) => {
    const newDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    setSelectedDate(newDate);
  };

  const handlePatientClick = (patient: PatientDto) => {
    onSelectPatient(patient);
    // 선택 후 사이드바 닫기 (선택 사항, UX에 따라 제거 가능)
    // onClose(); 
  };

  // --- Calendar Logic ---
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    return { daysInMonth: lastDay.getDate(), startDayOfWeek: firstDay.getDay() };
  };

  const { daysInMonth, startDayOfWeek } = getDaysInMonth(currentMonth);
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  if (!isOpen) return null;

  return (
    <>
      {/* 배경 오버레이 */}
      <div className="fixed inset-0 bg-black/50 z-[1500]" onClick={onClose} />

      {/* 사이드바 컨테이너 */}
      <div className={cn(
        "fixed left-0 top-0 h-full w-[320px] bg-[#d4d0c8] border-r-2 border-white z-[2000] transition-transform font-['Gulim'] text-[11px] shadow-2xl",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full">

          {/* 1. 타이틀 바 */}
          <div className="bg-[#000080] p-[4px] flex items-center justify-between text-white shrink-0">
            <span className="font-bold pl-1">▣ 환자 예약 관리</span>
            <button
              onClick={onClose}
              className="w-[18px] h-[18px] bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] text-black text-[11px] leading-none flex items-center justify-center cursor-pointer active:border-t-[#404040] active:border-l-[#404040]"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 flex flex-col p-[10px] overflow-hidden gap-2">

            {/* 2. 의사 정보 패널 */}
            <div className="bg-white border-2 border-[#808080] border-r-white border-b-white p-[8px]">
              <div className="font-bold text-[#000080] mb-[3px] border-b border-gray-200 pb-1">[담당의 정보]</div>
              <div>성명: {doctorInfo.name}</div>
              <div>소속: {doctorInfo.department}</div>
            </div>

            {/* 3. 예약 캘린더 */}
            <div className="bg-white border-2 border-[#808080] border-r-white border-b-white relative min-h-[180px]">

              {/* 로딩 오버레이 */}
              {isCalendarLoading && (
                <div className="absolute inset-0 z-10 bg-white/80 flex items-center justify-center">
                  <span className="text-blue-800 font-bold animate-pulse">Loading...</span>
                </div>
              )}

              {/* 달력 헤더 */}
              <div className="bg-[#000080] text-white p-[4px] flex items-center justify-between mb-1">
                <button onClick={() => changeMonth(-1)} className="w-[20px] bg-[#d4d0c8] text-black text-[10px] border border-white hover:bg-gray-200">◀</button>
                <span className="font-bold">{currentMonth.getFullYear()}년 {currentMonth.getMonth() + 1}월</span>
                <button onClick={() => changeMonth(1)} className="w-[20px] bg-[#d4d0c8] text-black text-[10px] border border-white hover:bg-gray-200">▶</button>
              </div>

              {/* 요일 헤더 */}
              <div className="grid grid-cols-7 border-b border-[#ececec] mb-1">
                {weekDays.map((day, i) => (
                  <div key={day} className={cn(
                    "text-center py-[2px] font-bold text-[10px]",
                    i === 0 && "text-red-600",
                    i === 6 && "text-blue-600"
                  )}>{day}</div>
                ))}
              </div>

              {/* 달력 그리드 */}
              <div className="grid grid-cols-7">
                {/* [수정] 빈 칸 Key 중복 해결 */}
                {Array.from({ length: startDayOfWeek }).map((_, i) => (
                  <div key={`empty-${i}`} className="h-[24px]" />
                ))}

                {/* [수정] 날짜 칸 Key 중복 해결 */}
                {Array.from({ length: daysInMonth }).map((_, i) => {
                  const day = i + 1;
                  const dayOfWeek = (startDayOfWeek + i) % 7;

                  const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                  const isReserved = reservedDates.includes(dateStr);

                  const isSelected = selectedDate.getDate() === day && selectedDate.getMonth() === currentMonth.getMonth();
                  const isToday = new Date().getDate() === day && new Date().getMonth() === currentMonth.getMonth();

                  return (
                    <div
                      key={`day-${day}`}
                      onClick={() => handleDayClick(day)}
                      className={cn(
                        "h-[24px] flex items-center justify-center cursor-pointer text-[10px] relative border border-transparent hover:border-gray-300",
                        dayOfWeek === 0 && "text-red-600",
                        dayOfWeek === 6 && "text-blue-600",
                        isSelected && "bg-[#000080] text-white hover:bg-[#000080] hover:text-white",
                        !isSelected && isToday && "bg-[#ffffcc] font-bold",
                        !isSelected && !isToday && "hover:bg-[#d4d0c8]"
                      )}
                    >
                      {day}
                      {/* 예약 점 표시 */}
                      {isReserved && !isSelected && (
                        <span className="absolute bottom-[2px] w-[4px] h-[4px] bg-red-500 rounded-full" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 4. 환자 리스트 */}
            <div className="flex-1 flex flex-col min-h-0 bg-white border-2 border-[#808080] border-r-white border-b-white">
              <div className="bg-[#000080] text-white px-2 py-1 font-bold shrink-0 text-[11px]">
                ▣ {formatDate(selectedDate)} 예약 환자
              </div>

              <div className="flex-1 overflow-y-auto p-1">
                {isLoading ? (
                  <div className="p-4 text-center text-gray-500">목록 로딩 중...</div>
                ) : patients.length === 0 ? (
                  <div className="p-4 text-center text-gray-500 text-[10px]">
                    예약된 환자가 없습니다.
                  </div>
                ) : (
                  patients.map((patient, index) => (
                    <div
                      key={patient.childId} // 고유 ID 사용
                      onClick={() => handlePatientClick(patient)}
                      className="group flex justify-between items-center p-1.5 border-b border-[#ececec] cursor-pointer hover:bg-[#000080] hover:text-white transition-colors"
                    >
                      {/* [수정] DTO 필드명 수정 (childName, months) */}
                      <div className="truncate font-bold">
                        {index + 1}. {patient.childName}
                      </div>
                      <div className="text-[10px] text-gray-500 group-hover:text-gray-200">
                        ({patient.gender === "MALE" ? "남" : "여"}/{patient.months}m)
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* 5. 하단 상태바 */}
            <div className="bg-white border-2 border-[#808080] border-r-white border-b-white p-[4px] text-right text-gray-600 shrink-0">
              Current Time: {currentTime}
            </div>

          </div>
        </div>
      </div>
    </>
  );
}