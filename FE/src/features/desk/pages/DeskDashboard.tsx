import { useState, useMemo } from "react";
import { Search, RotateCcw, Plus, Mail, X } from "lucide-react";
import DeskSidebar from "../components/DeskSidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";

// [탭 1] 초대 코드 미등록 환아
interface InviteCodePatientItem {
  inviteCodeId: string;
  childName: string;
  childMonths: number;
  parentPhone: string;
  scheduledAt: string;
  status: "ISSUED" | "REGISTERED" | "EXPIRED" | "REVOKED";
  inviteCode: string;
}

// [탭 2] 검사 등록 환아
interface ReservationChildItem {
  hospitalChildrenId: string;
  childId: string;
  name: string;
  months: number;
  gender: "MALE" | "FEMALE";
  examStatus: "IN_PROGRESS" | "COMPLETED";
  isSubmitted: boolean;
  scheduledAt: string;
  parentPhone: string;
  birthDate: string;
}

export default function DeskDashboard() {
  const [activeTab, setActiveTab] = useState<"UNREGISTERED" | "REGISTERED">(
    "UNREGISTERED",
  );
  const [selectedDate, setSelectedDate] = useState<Date>(
    new Date("2026-01-19"),
  );

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

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

  const handleSearchClick = () => {
    setAppliedFilters({ ...filters });
    setSelectedIds(new Set());
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
    setSelectedIds(new Set());
  };

  const handleDelete = (id: string) => {
    if (activeTab === "UNREGISTERED") {
      setUnregisteredList((prev) =>
        prev.filter((item) => item.inviteCodeId !== id),
      );
    } else {
      setRegisteredList((prev) =>
        prev.filter((item) => item.hospitalChildrenId !== id),
      );
    }

    if (selectedIds.has(id)) {
      const newSelected = new Set(selectedIds);
      newSelected.delete(id);
      setSelectedIds(newSelected);
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = filteredList.map((item: any) =>
        activeTab === "UNREGISTERED"
          ? item.inviteCodeId
          : item.hospitalChildrenId,
      );
      setSelectedIds(new Set(allIds));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectOne = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

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

  // --- Filtering Logic ---
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
      if (appliedFilters.status !== "all")
        list = list.filter((p) => p.status === appliedFilters.status);
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
      if (appliedFilters.status !== "all")
        list = list.filter((p) => p.examStatus === appliedFilters.status);
    }

    return { filteredList: list, calendarPoints: points };
  }, [
    activeTab,
    selectedDate,
    appliedFilters,
    unregisteredList,
    registeredList,
  ]);

  const isAllSelected =
    filteredList.length > 0 && filteredList.length === selectedIds.size;

  return (
    <div className="flex min-h-screen bg-[#F9FAFB] font-['Pretendard',sans-serif]">
      <DeskSidebar
        selectedDate={selectedDate}
        onDateSelect={handleSidebarDateSelect}
        reservationDates={calendarPoints}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <header className="px-10 pt-10 pb-0 bg-white border-b border-gray-200">
          <div className="flex justify-between items-center mb-2">
            <h1 className="text-2xl font-bold text-[#1A1A1A]">환자 관리</h1>

            <Button className="bg-white hover:bg-gray-50 text-[#5A55D6] border border-[#5A55D6] font-bold h-10 gap-2 shadow-sm">
              <Plus className="w-4 h-4" />
              초대 코드 발급
            </Button>
          </div>
          <p className="text-gray-500 text-sm mb-8">
            초대코드 및 분석을 미진행한 환자를 조회합니다
          </p>

          <div className="flex gap-8">
            <button
              onClick={() => {
                setActiveTab("UNREGISTERED");
                handleResetSearch();
              }}
              className={`pb-3 text-sm font-bold transition-all border-b-2 ${
                activeTab === "UNREGISTERED"
                  ? "text-[#5A55D6] border-[#5A55D6]"
                  : "text-gray-400 border-transparent hover:text-gray-600"
              }`}
            >
              초대 코드 미등록자
            </button>
            <button
              onClick={() => {
                setActiveTab("REGISTERED");
                handleResetSearch();
              }}
              className={`pb-3 text-sm font-bold transition-all border-b-2 ${
                activeTab === "REGISTERED"
                  ? "text-[#5A55D6] border-[#5A55D6]"
                  : "text-gray-400 border-transparent hover:text-gray-600"
              }`}
            >
              검사 등록자
            </button>
          </div>
        </header>

        <div className="p-10">
          <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-wrap items-center gap-4 mb-6 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-600 shrink-0">
                환자명
              </span>
              <Input
                placeholder="김누구"
                className="w-32 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
                value={filters.name}
                onChange={(e) =>
                  setFilters({ ...filters, name: e.target.value })
                }
                onKeyDown={(e) => e.key === "Enter" && handleSearchClick()}
              />
            </div>

            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-600 shrink-0">
                환자생년월일
              </span>
              <Input
                placeholder="2026.01.01"
                className="w-36 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
                value={filters.birthDate}
                onChange={(e) =>
                  setFilters({ ...filters, birthDate: e.target.value })
                }
                onKeyDown={(e) => e.key === "Enter" && handleSearchClick()}
              />
            </div>

            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-600 shrink-0">
                보호자 전화번호
              </span>
              <Input
                placeholder="010-1234-5678"
                className="w-40 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
                value={filters.phone}
                onChange={(e) =>
                  setFilters({ ...filters, phone: e.target.value })
                }
                onKeyDown={(e) => e.key === "Enter" && handleSearchClick()}
              />
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
            {activeTab === "UNREGISTERED" && (
              <>
                <div className="flex items-center bg-gray-50 px-6 py-4 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-wider">
                  <div className="w-[5%]">
                    <Checkbox
                      checked={isAllSelected}
                      onCheckedChange={(checked) =>
                        handleSelectAll(checked as boolean)
                      }
                    />
                  </div>
                  <div className="w-[15%]">환자 정보</div>
                  <div className="w-[10%] text-center">나이</div>
                  <div className="w-[15%] text-center">예약일</div>
                  <div className="w-[20%] text-center">초대코드 상태</div>
                  <div className="w-[15%] text-center">초대코드</div>
                  <div className="w-[20%] text-right">관리</div>
                </div>
                <div className="divide-y divide-gray-100">
                  {filteredList.length > 0 ? (
                    filteredList.map((patient: InviteCodePatientItem) => (
                      <div
                        key={patient.inviteCodeId}
                        className="flex items-center px-6 py-5 hover:bg-gray-50/50 transition-colors"
                      >
                        <div className="w-[5%]">
                          <Checkbox
                            checked={selectedIds.has(patient.inviteCodeId)}
                            onCheckedChange={() =>
                              handleSelectOne(patient.inviteCodeId)
                            }
                          />
                        </div>
                        <div className="w-[15%]">
                          <span className="text-base font-bold text-[#1A1A1A]">
                            {patient.childName}
                          </span>
                          <div className="text-xs text-gray-400 mt-0.5">
                            {patient.parentPhone}
                          </div>
                        </div>
                        <div className="w-[10%] text-center text-sm text-gray-700">
                          {patient.childMonths}개월
                        </div>
                        <div className="w-[15%] text-center text-sm text-gray-800">
                          {patient.scheduledAt.split("T")[0]}
                        </div>
                        <div className="w-[20%] text-center">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-bold ${
                              patient.status === "ISSUED"
                                ? "bg-blue-50 text-blue-600"
                                : patient.status === "REVOKED"
                                  ? "bg-red-50 text-red-600"
                                  : "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {patient.status === "ISSUED"
                              ? "미등록"
                              : patient.status === "REVOKED"
                                ? "취소됨"
                                : "등록완료"}
                          </span>
                        </div>
                        <div className="w-[15%] text-center text-sm font-mono text-gray-600">
                          {patient.inviteCode}
                        </div>
                        <div className="w-[20%] flex justify-end gap-2 items-center">
                          {/* ✨ [수정] 재전송 버튼: 아이콘 추가 + 하늘색 변경 */}
                          <Button className="bg-sky-500 hover:bg-sky-600 h-8 px-3 text-xs font-bold text-white gap-1">
                            <Mail className="w-3 h-3" />
                            재전송
                          </Button>

                          <button
                            onClick={() => handleDelete(patient.inviteCodeId)}
                            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <EmptyState date={formatDateDot(selectedDate)} />
                  )}
                </div>
              </>
            )}

            {activeTab === "REGISTERED" && (
              <>
                <div className="flex items-center bg-gray-50 px-6 py-4 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-wider">
                  <div className="w-[5%]">
                    <Checkbox
                      checked={isAllSelected}
                      onCheckedChange={(checked) =>
                        handleSelectAll(checked as boolean)
                      }
                    />
                  </div>
                  <div className="w-[20%]">환자 정보</div>
                  <div className="w-[10%] text-center">나이</div>
                  <div className="w-[20%] text-center">예약일</div>
                  <div className="w-[15%] text-center">검사 상태</div>
                  <div className="w-[30%] text-right">안내 메시지</div>
                </div>
                <div className="divide-y divide-gray-100">
                  {filteredList.length > 0 ? (
                    filteredList.map((patient: ReservationChildItem) => (
                      <div
                        key={patient.hospitalChildrenId}
                        className="flex items-center px-6 py-5 hover:bg-gray-50/50 transition-colors"
                      >
                        <div className="w-[5%]">
                          <Checkbox
                            checked={selectedIds.has(
                              patient.hospitalChildrenId,
                            )}
                            onCheckedChange={() =>
                              handleSelectOne(patient.hospitalChildrenId)
                            }
                          />
                        </div>
                        <div className="w-[20%]">
                          <div className="flex items-center gap-2">
                            <span className="text-base font-bold text-[#1A1A1A]">
                              {patient.name}
                            </span>
                            <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                              {patient.gender === "MALE" ? "남아" : "여아"}
                            </span>
                          </div>
                          <div className="text-xs text-gray-400 mt-0.5">
                            {patient.parentPhone}
                          </div>
                        </div>
                        <div className="w-[10%] text-center text-sm text-gray-700">
                          {patient.months}개월
                        </div>
                        <div className="w-[20%] text-center text-sm text-gray-800">
                          {patient.scheduledAt.split("T")[0]}
                        </div>
                        <div className="w-[15%] text-center">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-bold ${
                              patient.examStatus === "COMPLETED"
                                ? "bg-blue-50 text-[#5A55D6]"
                                : "bg-orange-50 text-orange-600"
                            }`}
                          >
                            {patient.examStatus === "COMPLETED"
                              ? "완료"
                              : "미완료"}
                          </span>
                        </div>
                        <div className="w-[30%] flex justify-end gap-2">
                          {/* ✨ [수정] 전송 버튼: 하늘색 변경 (bg-sky-500) */}
                          <Button className="bg-sky-500 hover:bg-sky-600 text-white h-8 px-4 text-xs font-bold gap-1">
                            <Mail className="w-3 h-3" />
                            전송
                          </Button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <EmptyState date={formatDateDot(selectedDate)} />
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function EmptyState({ date }: { date: string }) {
  return (
    <div className="py-20 text-center flex flex-col items-center justify-center text-gray-400">
      <div className="text-lg font-bold mb-1">{date}</div>
      <p>해당 날짜에 조회된 환자가 없습니다.</p>
    </div>
  );
}
