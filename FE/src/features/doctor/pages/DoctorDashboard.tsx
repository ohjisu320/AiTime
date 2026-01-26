import { useState, useMemo } from "react";
import { Search, Eye, RotateCcw } from "lucide-react";
import DoctorSidebar from "../components/DoctorSidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface DoctorPatientItem {
  hospitalChildrenId: string;
  childName: string;
  gender: "MALE" | "FEMALE";
  months: number;
  scheduledAt: string;
  examStatus: "IN_PROGRESS" | "COMPLETED";
  isSubmitted: boolean;
  birthDate?: string;
  parentPhone?: string;
}

export default function DoctorDashboard() {
  const [activeTab, setActiveTab] = useState<"DAILY" | "ALL">("DAILY");
  const [selectedDate, setSelectedDate] = useState<Date>(new Date("2026-01-19"));

  const [filters, setFilters] = useState({
    name: "",
    birthDate: "",
    phone: "",
    status: "all",
  });

  const [appliedFilters, setAppliedFilters] = useState({
    name: "",
    birthDate: "",
    phone: "",
    status: "all",
  });

  const allPatients: DoctorPatientItem[] = [
    {
      hospitalChildrenId: "uuid-1",
      childName: "박지우",
      gender: "MALE",
      months: 15,
      scheduledAt: "2026-01-19T10:00:00",
      examStatus: "COMPLETED",
      isSubmitted: true,
      birthDate: "2024.10.19",
      parentPhone: "010-1234-5678"
    },
    {
      hospitalChildrenId: "uuid-2",
      childName: "이서준",
      gender: "MALE",
      months: 22,
      scheduledAt: "2026-01-19T11:30:00",
      examStatus: "COMPLETED",
      isSubmitted: true,
      birthDate: "2024.03.19",
      parentPhone: "010-1111-2222"
    },
    {
      hospitalChildrenId: "uuid-3",
      childName: "김하은",
      gender: "FEMALE",
      months: 17,
      scheduledAt: "2026-01-18T14:00:00",
      examStatus: "COMPLETED",
      isSubmitted: true,
      birthDate: "2024.08.18",
      parentPhone: "010-3333-4444"
    },
    {
      hospitalChildrenId: "uuid-4",
      childName: "최도윤",
      gender: "MALE",
      months: 19,
      scheduledAt: "2026-01-20T09:00:00",
      examStatus: "IN_PROGRESS",
      isSubmitted: false,
      birthDate: "2024.06.20",
      parentPhone: "010-5555-6666"
    },
    {
      hospitalChildrenId: "uuid-5",
      childName: "정수아",
      gender: "FEMALE",
      months: 16,
      scheduledAt: "2026-01-17T16:00:00",
      examStatus: "COMPLETED",
      isSubmitted: true,
      birthDate: "2024.09.17",
      parentPhone: "010-7777-8888"
    },
  ];

  // ✨ [추가] 환자 데이터에서 예약 날짜만 추출 (중복 제거)
  // 결과 예시: ["2026-01-19", "2026-01-18", "2026-01-20", "2026-01-17"]
  const reservationDates = useMemo(() => {
    const dates = allPatients.map((p) => p.scheduledAt.split("T")[0]);
    return Array.from(new Set(dates)); // 중복 제거
  }, [allPatients]);

  const handleSidebarDateSelect = (date: Date) => {
    setSelectedDate(date);
    setActiveTab("DAILY");
  };

  const handleSearchClick = () => {
    setAppliedFilters({ ...filters });
  };

  const handleResetSearch = () => {
    const initialFilters = {
      name: "",
      birthDate: "",
      phone: "",
      status: "all",
    };
    setFilters(initialFilters);
    setAppliedFilters(initialFilters);
  };

  const isSameDay = (dateStr: string, dateObj: Date) => {
    const d1 = new Date(dateStr);
    return (
      d1.getFullYear() === dateObj.getFullYear() &&
      d1.getMonth() === dateObj.getMonth() &&
      d1.getDate() === dateObj.getDate()
    );
  };

  const filteredPatients = useMemo(() => {
    let result = allPatients;

    if (activeTab === "DAILY") {
      result = result.filter((p) => isSameDay(p.scheduledAt, selectedDate));
    } else {
      const hasSearch = 
        appliedFilters.name || 
        appliedFilters.birthDate || 
        appliedFilters.phone || 
        appliedFilters.status !== "all";
      
      if (!hasSearch) {
        return [];
      }
    }

    if (appliedFilters.name) {
      result = result.filter(p => p.childName.includes(appliedFilters.name));
    }
    if (appliedFilters.birthDate) {
      result = result.filter(p => p.birthDate?.includes(appliedFilters.birthDate));
    }
    if (appliedFilters.phone) {
      result = result.filter(p => p.parentPhone?.includes(appliedFilters.phone));
    }
    if (appliedFilters.status !== "all") {
      result = result.filter(p => p.examStatus === appliedFilters.status);
    }

    return result;
  }, [activeTab, selectedDate, appliedFilters, allPatients]);

  const formatDateDot = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}.${m}.${d}`;
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    let hour = date.getHours();
    const minute = String(date.getMinutes()).padStart(2, "0");
    const ampm = hour >= 12 ? "오후" : "오전";
    hour = hour % 12 || 12; 
    return `${ampm} ${hour}:${minute}`;
  };

  const dailyTotalCount = allPatients.filter((p) => isSameDay(p.scheduledAt, selectedDate)).length;

  return (
    <div className="flex min-h-screen bg-[#F9FAFB] font-['Pretendard',sans-serif]">
      {/* ✨ [수정] reservationDates props 전달 */}
      <DoctorSidebar 
        selectedDate={selectedDate} 
        onDateSelect={handleSidebarDateSelect}
        reservationDates={reservationDates} 
      />

      <main className="flex-1 flex flex-col min-w-0">
        <header className="px-10 pt-10 pb-0 bg-white border-b border-gray-200">
          <h1 className="text-2xl font-bold text-[#1A1A1A] mb-2">
            환자 기록 & 분석
          </h1>
          <p className="text-gray-500 text-sm mb-8">
            전체 환자를 검색하고 AI 분석 결과를 확인하세요
          </p>

          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab("DAILY")}
              className={`pb-3 text-sm font-bold transition-all border-b-2 ${
                activeTab === "DAILY"
                  ? "text-[#5A55D6] border-[#5A55D6]"
                  : "text-gray-400 border-transparent hover:text-gray-600"
              }`}
            >
              일별 환자 ({dailyTotalCount})
            </button>
            <button
              onClick={() => setActiveTab("ALL")}
              className={`pb-3 text-sm font-bold transition-all border-b-2 ${
                activeTab === "ALL"
                  ? "text-[#5A55D6] border-[#5A55D6]"
                  : "text-gray-400 border-transparent hover:text-gray-600"
              }`}
            >
              전체 조회
            </button>
          </div>
        </header>

        <div className="p-10">
          <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-wrap items-center gap-4 mb-6 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-600 shrink-0">환자명</span>
              <Input
                placeholder="김누구"
                className="w-32 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
                value={filters.name}
                onChange={(e) => setFilters({ ...filters, name: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchClick()}
              />
            </div>

            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-600 shrink-0">생년월일</span>
              <Input
                placeholder="2026.01.01"
                className="w-36 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
                value={filters.birthDate}
                onChange={(e) => setFilters({ ...filters, birthDate: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchClick()}
              />
            </div>

            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-600 shrink-0">보호자 전화번호</span>
              <Input
                placeholder="010-1234-5678"
                className="w-40 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
                value={filters.phone}
                onChange={(e) => setFilters({ ...filters, phone: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchClick()}
              />
            </div>

            <div className="flex items-center gap-3">
               <div className="w-px h-6 bg-gray-200 mx-2"></div>
               <Select 
                 value={filters.status}
                 onValueChange={(val) => setFilters({ ...filters, status: val })}
               >
                <SelectTrigger className="w-32 h-10 bg-gray-50 border-gray-200 text-gray-600">
                  <SelectValue placeholder="분석상태" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="COMPLETED">분석완료</SelectItem>
                  <SelectItem value="IN_PROGRESS">대기</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="ml-auto flex gap-2">
              <Button 
                variant="outline"
                onClick={handleResetSearch}
                className="h-10 px-4 text-sm font-bold text-gray-600 border-gray-300 hover:bg-gray-50"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                초기화
              </Button>
              <Button 
                onClick={handleSearchClick}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 h-10 px-6 text-sm font-bold shadow-sm transition-colors"
              >
                <Search className="w-4 h-4 mr-2" />
                검색하기
              </Button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="flex items-center bg-gray-50 px-8 py-4 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-wider">
              <div className="w-[20%]">환자 정보</div>
              <div className="w-[15%] text-center">나이</div>
              <div className="w-[25%] text-center">예약일</div>
              <div className="w-[20%] text-center">상태</div>
              <div className="w-[20%] text-right">액션</div>
            </div>

            <div className="divide-y divide-gray-100">
              {filteredPatients.length > 0 ? (
                filteredPatients.map((patient) => (
                  <div
                    key={patient.hospitalChildrenId}
                    className="flex items-center px-8 py-5 hover:bg-gray-50/50 transition-colors"
                  >
                    <div className="w-[20%]">
                      <div className="flex items-center gap-2">
                        <span className="text-base font-bold text-[#1A1A1A]">
                          {patient.childName}
                        </span>
                        <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                          {patient.gender === "MALE" ? "남아" : "여아"}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        ID: {patient.hospitalChildrenId.slice(0, 6)}...
                      </div>
                    </div>

                    <div className="w-[15%] text-center text-sm font-medium text-gray-700">
                      {patient.months}개월
                    </div>

                    <div className="w-[25%] text-center">
                      <div className="text-sm font-medium text-gray-800">
                        {patient.scheduledAt.split("T")[0]}
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {formatTime(patient.scheduledAt)}
                      </div>
                    </div>

                    <div className="w-[20%] flex justify-center">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold ${
                          patient.examStatus === "COMPLETED"
                            ? "bg-blue-50 text-[#5A55D6]"
                            : "bg-orange-50 text-orange-600"
                        }`}
                      >
                        {patient.examStatus === "COMPLETED" ? "분석완료" : "대기"}
                      </span>
                    </div>

                    <div className="w-[20%] flex justify-end">
                       {patient.examStatus === "COMPLETED" ? (
                        <Button className="bg-sky-500 hover:bg-sky-600 text-white h-9 px-4 rounded-lg gap-2 shadow-sm transition-all">
                          <Eye className="w-4 h-4" />
                          <span className="text-xs font-bold">분석 보기</span>
                        </Button>
                      ) : (
                        <Button
                          disabled
                          className="bg-gray-400 h-9 px-4 rounded-lg gap-2 text-white opacity-50 cursor-not-allowed"
                        >
                          <Eye className="w-4 h-4" />
                          <span className="text-xs font-bold">분석 대기</span>
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-20 text-center flex flex-col items-center justify-center text-gray-400">
                  {activeTab === "ALL" && !appliedFilters.name && !appliedFilters.birthDate && !appliedFilters.phone && appliedFilters.status === 'all' ? (
                     <>
                        <Search className="w-10 h-10 mb-3 opacity-20" />
                        <p>검색 조건을 입력하여 환자를 조회해주세요.</p>
                     </>
                  ) : (
                    <>
                        {activeTab === "DAILY" && <div className="text-lg font-bold mb-1">{formatDateDot(selectedDate)}</div>}
                        <p>조건에 맞는 환자가 없습니다.</p>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}