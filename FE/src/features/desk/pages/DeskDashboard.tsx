import { useState, useMemo } from "react";
import { Plus } from "lucide-react";

// 공용 컴포넌트 import
import AppSidebar from "@/components/common/AppSidebar";
import SearchBar from "@/components/common/SearchBar";
import DashboardHeader, {
  type DashboardTab,
} from "@/components/common/DashboardHeader";

// 데스크 전용 리스트 컴포넌트 import
import DeskUnregisteredList, {
  type InviteCodePatientItem,
} from "../components/DeskUnregisteredList";
import DeskRegisteredList, {
  type ReservationChildItem,
} from "../components/DeskRegisteredList";

// UI 컴포넌트
import { Button } from "@/components/ui/button";

export default function DeskDashboard() {
  const [activeTab, setActiveTab] = useState<"UNREGISTERED" | "REGISTERED">(
    "UNREGISTERED",
  );
  const [selectedDate, setSelectedDate] = useState<Date>(
    new Date("2026-01-19"),
  );
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // 검색 필터 상태
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

  // Mock Data (미등록자)
  const [unregisteredList, setUnregisteredList] = useState<
    InviteCodePatientItem[]
  >([
    {
      inviteCodeId: "inv-1",
      childName: "김미등록",
      childMonths: 15,
      parentPhone: "010-1111-2222",
      scheduledAt: "2026-01-19T10:00:00",
      status: "ISSUED",
      inviteCode: "AB12-34CD",
    },
    {
      inviteCodeId: "inv-2",
      childName: "이대기",
      childMonths: 20,
      parentPhone: "010-3333-4444",
      scheduledAt: "2026-01-19T14:00:00",
      status: "ISSUED",
      inviteCode: "EF56-78GH",
    },
    {
      inviteCodeId: "inv-3",
      childName: "박취소",
      childMonths: 18,
      parentPhone: "010-5555-6666",
      scheduledAt: "2026-01-20T11:00:00",
      status: "REVOKED",
      inviteCode: "IJ90-12KL",
    },
  ]);

  // Mock Data (등록자)
  const [registeredList, setRegisteredList] = useState<ReservationChildItem[]>([
    {
      hospitalChildrenId: "h-child-1",
      childId: "child-1",
      name: "박지우",
      months: 15,
      gender: "MALE",
      examStatus: "COMPLETED",
      isSubmitted: true,
      scheduledAt: "2026-01-19T10:00:00",
      parentPhone: "010-1234-5678",
      birthDate: "2024.10.19",
    },
    {
      hospitalChildrenId: "h-child-2",
      childId: "child-2",
      name: "최수아",
      months: 22,
      gender: "FEMALE",
      examStatus: "IN_PROGRESS",
      isSubmitted: false,
      scheduledAt: "2026-01-19T15:00:00",
      parentPhone: "010-9876-5432",
      birthDate: "2024.03.19",
    },
    {
      hospitalChildrenId: "h-child-3",
      childId: "child-3",
      name: "정민준",
      months: 18,
      gender: "MALE",
      examStatus: "COMPLETED",
      isSubmitted: true,
      scheduledAt: "2026-01-20T09:30:00",
      parentPhone: "010-5555-7777",
      birthDate: "2024.07.20",
    },
  ]);

  // --- Handlers ---
  const handleSidebarDateSelect = (date: Date) => {
    setSelectedDate(date);
    setSelectedIds(new Set());
  };
  const handleFilterChange = (key: string, value: string) =>
    setFilters((prev) => ({ ...prev, [key]: value }));
  const handleSearchClick = () => {
    setAppliedFilters({ ...filters });
    setSelectedIds(new Set());
  };

  const handleResetSearch = () => {
    const initial = { name: "", birthDate: "", phone: "", status: "all" };
    setFilters(initial);
    setAppliedFilters(initial);
    setSelectedIds(new Set());
  };

  const handleTabChange = (value: string) => {
    setActiveTab(value as "UNREGISTERED" | "REGISTERED");
    handleResetSearch();
  };

  // 삭제 핸들러
  const handleDelete = (id: string) => {
    if (activeTab === "UNREGISTERED")
      setUnregisteredList((prev) =>
        prev.filter((item) => item.inviteCodeId !== id),
      );
    else
      setRegisteredList((prev) =>
        prev.filter((item) => item.hospitalChildrenId !== id),
      );

    if (selectedIds.has(id)) {
      const newSelected = new Set(selectedIds);
      newSelected.delete(id);
      setSelectedIds(newSelected);
    }
  };

  // 전체 선택 핸들러
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = filteredList.map((item: any) =>
        activeTab === "UNREGISTERED"
          ? item.inviteCodeId
          : item.hospitalChildrenId,
      );
      setSelectedIds(new Set(allIds));
    } else setSelectedIds(new Set());
  };

  // 개별 선택 핸들러
  const handleSelectOne = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) newSelected.delete(id);
    else newSelected.add(id);
    setSelectedIds(newSelected);
  };

  // --- Filtering Logic ---
  const isSameDay = (dateStr: string, dateObj: Date) => {
    const d1 = new Date(dateStr);
    return (
      d1.getFullYear() === dateObj.getFullYear() &&
      d1.getMonth() === dateObj.getMonth() &&
      d1.getDate() === dateObj.getDate()
    );
  };

  const formatDateDot = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}.${m}.${d}`;
  };

  // 리스트 필터링 및 달력 점(mark) 계산
  const { filteredList, calendarPoints } = useMemo(() => {
    let list: any[] = [];
    let points: string[] = [];

    if (activeTab === "UNREGISTERED") {
      list = unregisteredList.filter((p) =>
        isSameDay(p.scheduledAt, selectedDate),
      );
      points = Array.from(
        new Set(unregisteredList.map((p) => p.scheduledAt.split("T")[0])),
      );

      if (appliedFilters.name)
        list = list.filter((p) => p.childName.includes(appliedFilters.name));
      if (appliedFilters.phone)
        list = list.filter((p) => p.parentPhone.includes(appliedFilters.phone));
    } else {
      list = registeredList.filter((p) =>
        isSameDay(p.scheduledAt, selectedDate),
      );
      points = Array.from(
        new Set(registeredList.map((p) => p.scheduledAt.split("T")[0])),
      );

      if (appliedFilters.name)
        list = list.filter((p) => p.name.includes(appliedFilters.name));
      if (appliedFilters.phone)
        list = list.filter((p) => p.parentPhone.includes(appliedFilters.phone));
      if (appliedFilters.birthDate)
        list = list.filter((p) =>
          p.birthDate.includes(appliedFilters.birthDate),
        );
    }
    return { filteredList: list, calendarPoints: points };
  }, [
    activeTab,
    selectedDate,
    appliedFilters,
    unregisteredList,
    registeredList,
  ]);

  // 탭 설정
  const deskTabs: DashboardTab[] = [
    { value: "UNREGISTERED", label: "초대 코드 미등록자" },
    { value: "REGISTERED", label: "검사 등록자" },
  ];

  return (
    <div className="flex min-h-screen bg-[#F9FAFB] font-['Pretendard',sans-serif]">
      {/* 1. 사이드바 */}
      <AppSidebar
        selectedDate={selectedDate}
        onDateSelect={handleSidebarDateSelect}
        markedDates={calendarPoints}
        userInfo={{
          name: "김접수",
          roleLabel: "병원 관리자 (데스크)",
          systemLabel: "접수처 시스템",
        }}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {/* 2. 헤더 */}
        <DashboardHeader
          title="환자 관리"
          description="초대코드 및 분석을 미진행한 환자를 조회합니다"
          tabs={deskTabs}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        >
          <Button className="bg-white hover:bg-gray-50 text-[#5A55D6] border border-[#5A55D6] font-bold h-10 gap-2 shadow-sm">
            <Plus className="w-4 h-4" /> 초대 코드 발급
          </Button>
        </DashboardHeader>

        <div className="p-10">
          {/* 3. 검색바 */}
          <SearchBar
            filters={filters}
            onFilterChange={handleFilterChange}
            onSearch={handleSearchClick}
            onReset={handleResetSearch}
          />

          {/* 4. 리스트 (탭에 따라 전환) */}
          {activeTab === "UNREGISTERED" ? (
            <DeskUnregisteredList
              patients={filteredList}
              selectedIds={selectedIds}
              onSelectAll={handleSelectAll}
              onSelectOne={handleSelectOne}
              onDelete={handleDelete}
              dateLabel={formatDateDot(selectedDate)}
              emptyMessage="해당 날짜에 조회된 환자가 없습니다."
            />
          ) : (
            <DeskRegisteredList
              patients={filteredList}
              selectedIds={selectedIds}
              onSelectAll={handleSelectAll}
              onSelectOne={handleSelectOne}
              dateLabel={formatDateDot(selectedDate)}
              emptyMessage="해당 날짜에 조회된 환자가 없습니다."
            />
          )}
        </div>
      </main>
    </div>
  );
}
