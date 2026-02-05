import { Plus } from "lucide-react";

// 공용 컴포넌트 import
import AppSidebar from "@/components/common/AppSidebar";
import SearchBar from "@/components/common/SearchBar";
import DashboardHeader, {
  type DashboardTab,
} from "@/components/common/DashboardHeader";

// 데스크 전용 리스트 컴포넌트 import
import DeskUnregisteredList from "../components/DeskUnregisteredList"; // Type is inferred or imported internally if needed, logic moved to hook so strict type usage here might be less critical or handled via hook return type

// 모달 컴포넌트 import
import InviteCodeModal from "../components/modal/InviteCodeModal";
import InviteCodeResultModal from "../components/modal/InviteCodeResultModal";

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

// Custom Hook
import { useDeskDashboard } from "../hooks/useDeskDashboard";

export default function DeskDashboard() {
  const { state, actions } = useDeskDashboard();
  const {
    activeTab,
    selectedDate,
    selectedIds,
    userInfo,
    scheduledDates,
    isModalOpen,
    isResultModalOpen,
    resultModalData,
    modalError,
    deleteTargetId,
    filters,
    filteredList,
    dateLabel
  } = state;

  const {
    setActiveTab,
    setSelectedDate,
    setFilters,
    setIsModalOpen,
    setIsResultModalOpen,
    setModalError,
    setDeleteTargetId,
    handleSearchClick,
    handleResetSearch,
    handleSelectOne,
    handleDelete,
    handleConfirmDelete,
    handleCreateInviteCode,
    handleMonthChange,
    onSelectAllChange
  } = actions;

  // 탭 설정
  const deskTabs: DashboardTab[] = [
    { value: "UNREGISTERED", label: "초대 코드 미등록자" },
  ];

  return (
    <div className="flex min-h-screen bg-[#F9FAFB] font-['Pretendard',sans-serif]">
      {/* 1. 사이드바 */}
      <AppSidebar
        selectedDate={selectedDate}
        onDateSelect={setSelectedDate}
        markedDates={scheduledDates}
        onMonthChange={handleMonthChange}
        userInfo={userInfo}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {/* 2. 헤더 */}
        <DashboardHeader
          title="환자 관리"
          description="초대코드 및 분석을 미진행한 환자를 조회합니다"
          tabs={deskTabs}
          activeTab={activeTab}
          onTabChange={(val) => setActiveTab(val)}
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
            onFilterChange={setFilters}
            onSearch={handleSearchClick}
            onReset={handleResetSearch}
          />

          {/* 4. 리스트 (탭에 따라 전환) */}
          <DeskUnregisteredList
            patients={filteredList}
            selectedIds={selectedIds}
            onSelectAll={onSelectAllChange}
            onSelectOne={handleSelectOne}
            onDelete={handleDelete}
            dateLabel={dateLabel}
            emptyMessage="해당 날짜에 조회된 환자가 없습니다."
          />
        </div>
      </main>

      {/* 5. 모달 컴포넌트 연결 */}
      <InviteCodeModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setModalError(null);
        }}
        onConfirm={handleCreateInviteCode}
        apiError={modalError}
      />

      {/* 6. 결과 모달 */}
      <InviteCodeResultModal
        isOpen={isResultModalOpen}
        onClose={() => setIsResultModalOpen(false)}
        data={resultModalData}
      />

      {/* 7. 삭제 확인 모달 */}
      <AlertDialog
        open={!!deleteTargetId}
        onOpenChange={(open) => !open && setDeleteTargetId(null)}
      >
        <AlertDialogContent className="bg-white">
          <AlertDialogHeader>
            <AlertDialogTitle>초대코드 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말 이 초대코드를 삭제하시겠습니까? 삭제된 코드는 복구할 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteTargetId(null)}>
              취소
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-red-500 hover:bg-red-600 text-white border-0"
            >
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
