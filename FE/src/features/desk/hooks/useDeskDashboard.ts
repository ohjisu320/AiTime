import { useState, useMemo, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
    getUnregisteredPatients,
    createInviteCode,
    getScheduledDates,
    revokeInviteCode
} from "@/features/desk/api/inviteCodeApi";
import { getHospitalStaffProfile } from "@/features/desk/api/hospitalStaffApi";
import type { InviteCodePatientItem } from "../components/DeskUnregisteredList";

export const useDeskDashboard = () => {
    // --- States ---
    const [activeTab, setActiveTab] = useState<"UNREGISTERED" | "REGISTERED">("UNREGISTERED");
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    const [userInfo, setUserInfo] = useState(() => {
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
            try {
                const parsed = JSON.parse(savedUser);
                return {
                    name: parsed.name || "",
                    roleLabel: parsed.staffRole === "DOCTOR" ? "의사" : "병원 관리자",
                    systemLabel: "AiTime 병원" // 기본값 설정 (API로 업데이트)
                };
            } catch (e) {
                console.error("Failed to parse user info from localStorage", e);
            }
        }
        return {
            name: "",
            roleLabel: "",
            systemLabel: ""
        };
    });

    const [scheduledDates, setScheduledDates] = useState<string[]>([]);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isResultModalOpen, setIsResultModalOpen] = useState(false);
    const [resultModalData, setResultModalData] = useState<any>(null);
    const [modalError, setModalError] = useState<string | null>(null);
    const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

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

    const [unregisteredList, setUnregisteredList] = useState<InviteCodePatientItem[]>([]);

    // --- Helpers ---
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

    // --- API Handlers ---
    const fetchScheduledDates = useCallback(async (year: number, month: number) => {
        try {
            const response = await getScheduledDates(year, month);
            if (response.code === 200 && response.data) {
                setScheduledDates(response.data);
            }
        } catch (error) {
            console.error("❌ 예약 현황 조회 실패:", error);
        }
    }, []);

    const fetchUnregisteredPatients = useCallback(async (date: Date) => {
        try {
            const year = date.getFullYear();
            const month = date.getMonth() + 1;
            const day = date.getDate();

            console.log(`📅 [DeskDashboard] 날짜 선택됨: ${year}-${month}-${day}`);
            const response = await getUnregisteredPatients(year, month, day);

            if (response.code === 200 && response.data) {
                setUnregisteredList(response.data as unknown as InviteCodePatientItem[]);
            }
        } catch (error) {
            console.error("❌ [DeskDashboard] 미등록 환자 목록 로드 실패:", error);
        }
    }, []);

    // --- Side Effects ---
    // 초기 데이터 로드 (달력, 유저정보)
    useEffect(() => {
        const now = new Date();
        fetchScheduledDates(now.getFullYear(), now.getMonth() + 1);

        getHospitalStaffProfile().then(res => {
            if (res.code === 200 && res.data) {
                setUserInfo({
                    name: res.data.name,
                    roleLabel: res.data.role === "DOCTOR" ? "의사" : "병원 관리자",
                    systemLabel: res.data.hospitalName || "AiTime 병원"
                });
            }
        }).catch(err => console.error("❌ 유저 정보 조회 실패:", err));
    }, [fetchScheduledDates]);

    // 날짜 변경 시 리스트 로드
    useEffect(() => {
        if (activeTab === "UNREGISTERED") {
            fetchUnregisteredPatients(selectedDate);
        }
    }, [selectedDate, activeTab, fetchUnregisteredPatients]);

    // --- Event Handlers ---
    const handleMonthChange = useCallback((year: number, month: number) => {
        fetchScheduledDates(year, month);
    }, [fetchScheduledDates]);

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

    const handleSelectAll = (checked: boolean) => {
        if (checked) {
            // filteredList는 hook 내부에서 계산 필요
            const list = getFilteredList();
            const allIds = list.map((item) => item.inviteCodeId);
            setSelectedIds(new Set(allIds));
        } else {
            setSelectedIds(new Set());
        }
    };

    const handleSelectOne = (id: string) => {
        const newSelected = new Set(selectedIds);
        if (newSelected.has(id)) newSelected.delete(id);
        else newSelected.add(id);
        setSelectedIds(newSelected);
    };

    const handleDelete = (id: string) => setDeleteTargetId(id);

    const handleConfirmDelete = async () => {
        if (!deleteTargetId) return;

        try {
            const response = await revokeInviteCode(deleteTargetId);
            if (response.code === 200) {
                setUnregisteredList((prev) =>
                    prev.filter((item) => item.inviteCodeId !== deleteTargetId),
                );

                if (selectedIds.has(deleteTargetId)) {
                    const newSelected = new Set(selectedIds);
                    newSelected.delete(deleteTargetId);
                    setSelectedIds(newSelected);
                }

                const currentMonth = selectedDate.getMonth() + 1;
                fetchScheduledDates(selectedDate.getFullYear(), currentMonth);
                toast.success("초대코드가 삭제되었습니다.");
            }
        } catch (error: any) {
            console.error("❌ 초대코드 삭제 실패:", error);
            const msg = error.response?.data?.message || "삭제 중 오류가 발생했습니다.";
            toast.error(msg);
        } finally {
            setDeleteTargetId(null);
        }
    };

    const handleCreateInviteCode = async (data: any) => {
        setModalError(null);
        try {
            const requestData = {
                childName: data.childName.trim(),
                childBirthdate: data.childBirthdate.replace(/\./g, "-"),
                parentPhone: data.parentPhone.replace(/-/g, ""),
                scheduledAt: data.scheduledAt,
                doctorId: data.doctorId ? data.doctorId : undefined,
            };

            console.log("📤 [DeskDashboard] 초대코드 생성 요청 데이터:", requestData);
            const response = await createInviteCode(requestData);

            if (response.code === 201) {
                console.log("✅ [DeskDashboard] 초대코드 발급 성공:", response.data);

                const reservedDate = new Date(data.scheduledAt);
                const isSelectedDate = isSameDay(reservedDate.toISOString(), selectedDate);

                if (isSelectedDate && activeTab === "UNREGISTERED") {
                    await fetchUnregisteredPatients(selectedDate);
                }

                const currentMonth = selectedDate.getMonth() + 1;
                const reservedMonth = reservedDate.getMonth() + 1;
                if (currentMonth === reservedMonth) {
                    fetchScheduledDates(selectedDate.getFullYear(), currentMonth);
                }

                setIsModalOpen(false);
                setModalError(null);
                setResultModalData(response.data);
                setIsResultModalOpen(true);
            } else {
                console.warn("⚠️ [DeskDashboard] 초대코드 발급 성공 응답 아님:", response);
                setModalError(response.message || "알 수 없는 오류가 발생했습니다.");
            }
        } catch (error: any) {
            console.error("❌ [DeskDashboard] 초대코드 생성 실패:", error);
            const msg = error.response?.data?.message || "발급 중 오류가 발생했습니다.";
            setModalError(msg);
        }
    };

    // --- Filtering Logic (Moved inside hook to reuse in handleSelectAll) ---
    const getFilteredList = useCallback(() => {
        let list: InviteCodePatientItem[] = [];
        if (activeTab === "UNREGISTERED") {
            list = unregisteredList.filter((p) =>
                isSameDay(p.scheduledAt, selectedDate)
            );
            if (appliedFilters.name)
                list = list.filter((p) => p.childName.includes(appliedFilters.name));
            if (appliedFilters.phone) {
                const searchPhone = appliedFilters.phone.replace(/-/g, "");
                list = list.filter((p) => p.parentPhone.replace(/-/g, "").includes(searchPhone));
            }
        }
        return list;
    }, [activeTab, unregisteredList, selectedDate, appliedFilters]);

    const filteredList = useMemo(() => getFilteredList(), [getFilteredList]);

    return {
        state: {
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
            dateLabel: formatDateDot(selectedDate)
        },
        actions: {
            setActiveTab: handleTabChange,
            setSelectedDate: handleSidebarDateSelect,
            setFilters: handleFilterChange,
            setIsModalOpen,
            setIsResultModalOpen,
            setModalError,
            setDeleteTargetId,
            handleSearchClick,
            handleResetSearch,
            handleSelectAll: () => handleSelectAll(true), // Simplified for external usage if needed
            handleUnselectAll: () => handleSelectAll(false),
            handleSelectOne,
            handleDelete,
            handleConfirmDelete,
            handleCreateInviteCode,
            handleMonthChange,
            onSelectAllChange: handleSelectAll // For Checkbox
        }
    };
};
