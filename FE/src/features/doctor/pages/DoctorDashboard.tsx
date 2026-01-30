import { useState, useMemo } from "react";
// ❌ [삭제] 사용하지 않는 lucide-react 아이콘 제거
// import { Search, Eye, RotateCcw } from "lucide-react";

import AppSidebar from "@/components/common/AppSidebar";
import SearchBar from "@/components/common/SearchBar";
import DashboardHeader, {
  type DashboardTab,
} from "@/components/common/DashboardHeader";
import DoctorPatientList, {
  type DoctorPatientItem,
} from "../components/DoctorPatientList";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useNavigate } from "react-router-dom";


export default function DoctorDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"DAILY" | "ALL">("DAILY");
  const [selectedDate, setSelectedDate] = useState<Date>(
    new Date("2026-01-19"),
  );

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

  // Mock Data
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
      parentPhone: "010-1234-5678",
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
      parentPhone: "010-1111-2222",
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
      parentPhone: "010-3333-4444",
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
      parentPhone: "010-5555-6666",
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
      parentPhone: "010-7777-8888",
    },
  ];

  // --- Handlers ---
  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleSearchClick = () => {
    setAppliedFilters({ ...filters });
  };

  const handleResetSearch = () => {
    const initial = { name: "", birthDate: "", phone: "", status: "all" };
    setFilters(initial);
    setAppliedFilters(initial);
  };

  // --- Logic ---
  const reservationDates = useMemo(() => {
    const dates = allPatients.map((p) => p.scheduledAt.split("T")[0]);
    return Array.from(new Set(dates));
  }, [allPatients]);

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
      if (!hasSearch) return [];
    }
    if (appliedFilters.name)
      result = result.filter((p) => p.childName.includes(appliedFilters.name));
    if (appliedFilters.birthDate)
      result = result.filter((p) =>
        p.birthDate?.includes(appliedFilters.birthDate),
      );
    if (appliedFilters.phone)
      result = result.filter((p) =>
        p.parentPhone?.includes(appliedFilters.phone),
      );
    if (appliedFilters.status !== "all")
      result = result.filter((p) => p.examStatus === appliedFilters.status);
    return result;
  }, [activeTab, selectedDate, appliedFilters, allPatients]);

  const formatDateDot = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}.${m}.${d}`;
  };

  const dailyTotalCount = allPatients.filter((p) =>
    isSameDay(p.scheduledAt, selectedDate),
  ).length;

  const doctorTabs: DashboardTab[] = [
    { value: "DAILY", label: "일별 환자", count: dailyTotalCount },
    { value: "ALL", label: "전체 조회" },
  ];

  //  리포트 페이지 이동 핸들러
  const handleViewAnalysis = (hospitalChildrenId: string) => {
    navigate(`/doctor/report/${hospitalChildrenId}`);
  };

  return (
    <div className="flex min-h-screen bg-[#F9FAFB] font-['Pretendard',sans-serif]">
      <AppSidebar
        selectedDate={selectedDate}
        onDateSelect={(d) => {
          setSelectedDate(d);
          setActiveTab("DAILY");
        }}
        markedDates={reservationDates}
        userInfo={{
          name: "김의사",
          roleLabel: "소아청소년과 전문의",
          systemLabel: "의사용 시스템",
        }}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <DashboardHeader
          title="환자 기록 & 분석"
          description="전체 환자를 검색하고 AI 분석 결과를 확인하세요"
          tabs={doctorTabs}
          activeTab={activeTab}
          onTabChange={(val) => setActiveTab(val as "DAILY" | "ALL")}
        />

        <div className="p-10">
          <SearchBar
            filters={filters}
            onFilterChange={handleFilterChange}
            onSearch={handleSearchClick}
            onReset={handleResetSearch}
          >
            <div className="flex items-center gap-3">
              <div className="w-px h-6 bg-gray-200 mx-2"></div>
              <Select
                value={filters.status}
                onValueChange={(val) => handleFilterChange("status", val)}
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
          </SearchBar>

          <DoctorPatientList
            patients={filteredPatients}
            dateLabel={
              activeTab === "DAILY" ? formatDateDot(selectedDate) : undefined
            }
            emptyMessage={
              activeTab === "ALL" && !appliedFilters.name
                ? "검색 조건을 입력하여 환자를 조회해주세요."
                : "조건에 맞는 환자가 없습니다."
            }
            onViewAnalysis={handleViewAnalysis}
          />
        </div>
      </main>
    </div>
  );
}
