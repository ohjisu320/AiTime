import { useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import { doctorApi } from "../../api/doctorApi";
import type { PatientDto } from "../../types/doctor";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  waitingList: PatientDto[];  // 오늘 예약 환자 (부모에서 전달)
  onSelectPatient: (patient: PatientDto) => void;
  isLoading?: boolean;
}

export default function WaitingListSidebar({
  isOpen,
  onClose,
  waitingList,
  onSelectPatient,
  isLoading = false
}: Props) {
  const [currentTime, setCurrentTime] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<PatientDto[]>([]);
  const [isSearching, setIsSearching] = useState(false);

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

  // 검색 API 호출 (이름으로 전체 환자 검색)
  useEffect(() => {
    const searchPatients = async () => {
      if (searchTerm.trim().length === 0) {
        setSearchResults([]);
        return;
      }

      setIsSearching(true);
      try {
        // 날짜 없이 이름으로 전체 검색
        const response = await doctorApi.searchPatients({
          page: 0,
          size: 100,
          name: searchTerm.trim()
        });

        if (response.code === 200 && response.data?.childResponses) {
          setSearchResults(response.data.childResponses);
        } else {
          setSearchResults([]);
        }
      } catch (error) {
        console.error("환자 검색 실패:", error);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    };

    // 디바운스: 300ms 후 검색
    const timer = setTimeout(searchPatients, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // 표시할 목록: 검색 중이면 검색 결과, 아니면 오늘 예약 환자
  const displayList = searchTerm.trim() ? searchResults : waitingList;
  const listTitle = searchTerm.trim() ? "검색 결과" : "오늘 예약 환자";

  // 환자 클릭 핸들러
  const handlePatientClick = (patient: PatientDto) => {
    onSelectPatient(patient);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* 배경 오버레이 (클릭 시 닫힘) */}
      <div className="fixed inset-0 bg-black/50 z-[1500]" onClick={onClose} />

      {/* 사이드바 본체 */}
      <div
        className={cn(
          "fixed left-0 top-0 h-full w-[300px] bg-[#d4d0c8] border-r-2 border-white z-[2000] transition-transform font-['Gulim'] text-[11px]",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* 1. 타이틀 바 (닫기 버튼 포함) */}
          <div className="bg-[#000080] p-[4px] flex items-center justify-between text-white shrink-0">
            <span className="font-bold">▣ 환자 대기열</span>
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

            {/* 3. 대기열 검색 및 리스트 */}
            <div className="flex-1 flex flex-col min-h-0">
              <div className="font-bold mb-[5px]">▣ {listTitle}</div>
              <input
                type="text"
                placeholder="이름 검색 (전체 환자)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-[22px] bg-white border-2 border-[#808080] border-r-white border-b-white px-[3px] mb-[5px] text-[11px] outline-none"
              />

              <div className="flex-1 bg-white border-2 border-[#808080] border-r-white border-b-white overflow-y-auto mb-[10px]">
                {isLoading || isSearching ? (
                  <div className="p-[5px] text-center text-gray-500">로딩 중...</div>
                ) : displayList.length === 0 ? (
                  <div className="p-[5px] text-center text-gray-500">
                    {searchTerm.trim() ? "검색 결과 없음" : "대기 환자 없음"}
                  </div>
                ) : (
                  displayList.map((patient, index) => (
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

              {/* 4. 현재 시각 */}
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
