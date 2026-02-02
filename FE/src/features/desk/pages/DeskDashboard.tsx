import { useState, useMemo, useEffect } from "react";
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

// 모달 컴포넌트 import (경로 확인 필요)
import InviteCodeModal, {
  type InviteCodeFormData,
} from "../components/modal/InviteCodeModal";

// API
import { getUnregisteredPatients } from "@/features/desk/api/inviteCodeApi";

// UI 컴포넌트
import { Button } from "@/components/ui/button";

export default function DeskDashboard() {
  const [activeTab, setActiveTab] = useState<"UNREGISTERED" | "REGISTERED">(
    "UNREGISTERED",
  );
  const [selectedDate, setSelectedDate] = useState<Date>(
    new Date(), // 오늘 날짜로 초기화
  );
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // 모달 열림 상태 관리
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

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

  // 미등록자 리스트 (API)
  const [unregisteredList, setUnregisteredList] = useState<
    InviteCodePatientItem[]
  >([]);

  // Mock Data (등록자 - 추후 API 연동 필요)
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

  // --- API Fetching ---
  const fetchUnregisteredPatients = async (date: Date) => {
    try {
      setIsLoading(true);
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const day = date.getDate();

      console.log(`📅 [DeskDashboard] 날짜 선택됨: ${year}-${month}-${day}`);

      const response = await getUnregisteredPatients(year, month, day);
      console.log('✅ [DeskDashboard] API 응답:', response);

      if (response.code === 200 && response.data) {
        // API 응답을 UI 모델로 변환 (필드 매핑)
        const mappedList: InviteCodePatientItem[] = response.data.map(item => ({
          inviteCodeId: item.inviteCodeId,
          childName: item.childName,
          childMonths: item.childMonths,
          parentPhone: item.parentPhone,
          scheduledAt: item.scheduledAt,
          status: (item.status as any) || "ISSUED", // 타입 호환 처리
          inviteCode: "-" // API 응답에 코드가 없다면 공란 또는 별도 처리
        }));
        console.log(`📋 [DeskDashboard] 매핑된 리스트 (${mappedList.length}건):`, mappedList);
        setUnregisteredList(mappedList);
      }
    } catch (error) {
      console.error("❌ [DeskDashboard] 미등록 환자 목록 로드 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 날짜 변경 시 API 호출
  useEffect(() => {
    if (activeTab === "UNREGISTERED") {
      fetchUnregisteredPatients(selectedDate);
    }
  }, [selectedDate, activeTab]);

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

  // --- Modal Logic (데이터 추가) ---
  const handleCreateInviteCode = (data: InviteCodeFormData) => {
    // 1. 임시 데이터 생성 (실제 API 연동 시 서버 응답값 사용)
    const newItem: InviteCodePatientItem = {
      inviteCodeId: `inv-${Date.now()}`, // 임시 ID
      childName: data.childName,
      childMonths: 0, // 생년월일 기반 계산 로직 필요 (임시 0)
      parentPhone: data.parentPhone,
      // 예약 시간은 현재 선택된 날짜의 현재 시간으로 가정 (혹은 모달에서 입력받아야 함)
      scheduledAt: new Date(
        selectedDate.setHours(new Date().getHours()),
      ).toISOString(),
      status: "ISSUED", // 발급 상태
      inviteCode: Math.random().toString(36).substring(2, 10).toUpperCase(), // 랜덤 코드
    };

    // 2. 리스트 상태 업데이트 (최신순 추가)
    setUnregisteredList((prev) => [newItem, ...prev]);

    // 3. 탭을 '미등록자'로 전환하여 추가된 항목 확인
    setActiveTab("UNREGISTERED");

    // 4. 모달 닫기
    setIsModalOpen(false);

    // 5. 알림 (선택 사항)
    // alert(`${data.childName} 환자의 초대코드가 발급되었습니다.`);
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
          {/* 버튼 클릭 시 모달 Open */}
          <Button
            onClick={() => setIsModalOpen(true)}
            className="bg-white hover:bg-gray-50 text-[#5A55D6] border border-[#5A55D6] font-bold h-10 gap-2 shadow-sm"
          >
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

      {/* 5. 모달 컴포넌트 연결 */}
      <InviteCodeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleCreateInviteCode}
      />
    </div>
  );
}
