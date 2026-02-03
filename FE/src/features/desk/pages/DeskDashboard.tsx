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


// 모달 컴포넌트 import (경로 확인 필요)
import InviteCodeModal, {
  type InviteCodeFormData,
} from "../components/modal/InviteCodeModal";
import InviteCodeResultModal from "../components/modal/InviteCodeResultModal";

// API
import { getUnregisteredPatients, createInviteCode, getScheduledDates, revokeInviteCode } from "@/features/desk/api/inviteCodeApi";

// UI 컴포넌트
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";

export default function DeskDashboard() {
  const [activeTab, setActiveTab] = useState<"UNREGISTERED" | "REGISTERED">(
    "UNREGISTERED",
  );
  const [selectedDate, setSelectedDate] = useState<Date>(
    new Date(), // 오늘 날짜로 초기화
  );
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null); // 삭제 대상 ID (모달용)

  // 예약 현황(달력 점 표시) 상태
  const [scheduledDates, setScheduledDates] = useState<string[]>([]);

  // 달력 월 변경 핸들러
  const handleMonthChange = (year: number, month: number) => {
    fetchScheduledDates(year, month);
  };

  // 예약 현황 조회
  const fetchScheduledDates = async (year: number, month: number) => {
    try {
      const response = await getScheduledDates(year, month);
      if (response.code === 200 && response.data) {
        setScheduledDates(response.data);
      }
    } catch (error) {
      console.error("❌ 예약 현황 조회 실패:", error);
    }
  };

  // 초기 마운트 시 현재 월 데이터 조회
  useEffect(() => {
    const now = new Date();
    fetchScheduledDates(now.getFullYear(), now.getMonth() + 1);
  }, []);

  // 모달 열림 상태 관리
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isResultModalOpen, setIsResultModalOpen] = useState(false);
  const [resultModalData, setResultModalData] = useState<any>(null); // 결과 데이터
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

  // 삭제 클릭 핸들러 (모달 열기)
  const handleDelete = (id: string) => {
    setDeleteTargetId(id);
  };

  // 삭제 확인 핸들러 (API 호출)
  const handleConfirmDelete = async () => {
    if (!deleteTargetId) return;

    try {
      const response = await revokeInviteCode(deleteTargetId);
      if (response.code === 200) {
        // 성공 시 목록에서 제거
        setUnregisteredList((prev) =>
          prev.filter((item) => item.inviteCodeId !== deleteTargetId),
        );

        if (selectedIds.has(deleteTargetId)) {
          const newSelected = new Set(selectedIds);
          newSelected.delete(deleteTargetId);
          setSelectedIds(newSelected);
        }

        // 예약이 취소되었으므로 달력 점도 갱신 필요할 수 있음 (해당 월이면)
        fetchScheduledDates(selectedDate.getFullYear(), selectedDate.getMonth() + 1);

        toast.success("초대코드가 삭제되었습니다.");
      }
    } catch (error: any) {
      console.error("❌ 초대코드 삭제 실패:", error);
      const msg = error.response?.data?.message || "삭제 중 오류가 발생했습니다.";
      toast.error(msg);
    } finally {
      setDeleteTargetId(null); // 모달 닫기
    }
  };

  // 전체 선택 핸들러
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = filteredList.map((item: any) =>
        item.inviteCodeId
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
  // --- Modal Logic (데이터 추가) ---
  // --- Modal Logic (데이터 추가) ---
  // --- Modal Logic (데이터 추가) ---
  const handleCreateInviteCode = async (data: any) => { // TODO: 타입 정의 수정 필요 (InviteCodeFormData 확장)
    try {
      setIsLoading(true);

      const requestData = {
        childName: data.childName.trim(),
        childBirthdate: data.childBirthdate.replace(/\./g, "-"),
        parentPhone: data.parentPhone.replace(/-/g, ""),
        scheduledAt: data.scheduledAt, // 모달에서 이미 ISO string으로 변환되어 옴
        doctorId: data.doctorId ? data.doctorId : undefined, // 빈 문자열이나 null이면 undefined 처리 (JSON 제외)
      };

      console.log("📤 [DeskDashboard] 초대코드 생성 요청 데이터:", requestData);

      // 2. API 호출
      const response = await createInviteCode(requestData);

      if (response.code === 200) {
        console.log("✅ [DeskDashboard] 초대코드 발급 성공:", response.data);

        // 4. 리스트 갱신 
        // 선택된 예약일이 현재 대시보드의 '선택된 날짜'와 같다면 리스트갱신
        const reservedDate = new Date(data.scheduledAt);
        const isSelectedDate = isSameDay(reservedDate.toISOString(), selectedDate);

        if (isSelectedDate && activeTab === "UNREGISTERED") {
          await fetchUnregisteredPatients(selectedDate);
        }

        // **새로 추가**: 예약 후 캘린더 점 갱신 필요 (해당 월)
        const currentMonth = selectedDate.getMonth() + 1;
        const reservedMonth = reservedDate.getMonth() + 1;
        // 유저가 보고 있는 달력(selectedDate 기준)과 예약 날짜의 달이 같으면 갱신
        if (currentMonth === reservedMonth) {
          fetchScheduledDates(selectedDate.getFullYear(), currentMonth);
        }

        // 5. 모달 스위칭 (입력 모달 닫기 -> 결과 모달 열기)
        setIsModalOpen(false);
        setResultModalData(response.data);
        setIsResultModalOpen(true);
      }
    } catch (error: any) {
      console.error("❌ [DeskDashboard] 초대코드 생성 실패:", error);
      const msg = error.response?.data?.message || "발급 중 오류가 발생했습니다.";
      alert(msg);
    } finally {
      setIsLoading(false);
    }
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

  // 리스트 필터링
  const { filteredList } = useMemo(() => {
    let list: any[] = [];

    if (activeTab === "UNREGISTERED") {
      list = unregisteredList.filter((p) =>
        isSameDay(p.scheduledAt, selectedDate),
      );

      if (appliedFilters.name)
        list = list.filter((p) => p.childName.includes(appliedFilters.name));
      if (appliedFilters.phone)
        list = list.filter((p) => p.parentPhone.includes(appliedFilters.phone));
    }
    return { filteredList: list };
  }, [
    activeTab,
    selectedDate,
    appliedFilters,
    unregisteredList,
  ]);

  // 탭 설정
  const deskTabs: DashboardTab[] = [
    { value: "UNREGISTERED", label: "초대 코드 미등록자" },

  ];

  return (
    <div className="flex min-h-screen bg-[#F9FAFB] font-['Pretendard',sans-serif]">
      {/* 1. 사이드바 */}
      <AppSidebar
        selectedDate={selectedDate}
        onDateSelect={handleSidebarDateSelect}
        markedDates={scheduledDates} // API 데이터 연결
        onMonthChange={handleMonthChange} // 월 변경 핸들러
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
          <DeskUnregisteredList
            patients={filteredList}
            selectedIds={selectedIds}
            onSelectAll={handleSelectAll}
            onSelectOne={handleSelectOne}
            onDelete={handleDelete}
            dateLabel={formatDateDot(selectedDate)}
            emptyMessage="해당 날짜에 조회된 환자가 없습니다."
          />
        </div>
      </main>

      {/* 5. 모달 컴포넌트 연결 */}
      <InviteCodeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleCreateInviteCode}
      />

      {/* 6. 결과 모달 */}
      <InviteCodeResultModal
        isOpen={isResultModalOpen}
        onClose={() => setIsResultModalOpen(false)}
        data={resultModalData}
      />

      {/* 7. 삭제 확인 모달 */}
      <AlertDialog open={!!deleteTargetId} onOpenChange={(open) => !open && setDeleteTargetId(null)}>
        <AlertDialogContent className="bg-white">
          <AlertDialogHeader>
            <AlertDialogTitle>초대코드 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말 이 초대코드를 삭제하시겠습니까? 삭제된 코드는 복구할 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteTargetId(null)}>취소</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-red-500 hover:bg-red-600 text-white border-0">
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
