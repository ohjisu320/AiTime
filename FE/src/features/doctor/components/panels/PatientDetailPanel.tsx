import { useNavigate } from "react-router-dom";
import { logoutHospitalStaff } from "@/features/desk/api/hospitalStaffApi";
import type { PatientDetailFull } from "../../types/doctor";

interface Props {
  patient: PatientDetailFull | null;
  toggleSidebar: () => void;
}

export default function PatientDetailPanel({ patient, toggleSidebar }: Props) {
  const navigate = useNavigate();

  // 로그아웃 핸들러 (알림창 없이)
  const handleLogout = async () => {
    try {
      await logoutHospitalStaff();
    } catch (error) {
      console.error("로그아웃 API 실패:", error);
    } finally {
      // API 성공 여부와 관계없이 로컬 스토리지 클리어 후 로그인 페이지로 이동
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
      navigate("/login");
    }
  };

  // 환자 정보가 없을 때도 열기/로그아웃 버튼은 표시
  if (!patient) {
    return (
      <div className="flex flex-col h-full bg-[#f7f7f7] border-r border-[#808080] font-['Gulim'] text-[11px]">
        {/* 상단 열기 바 */}
        <div className="bg-[#000080] p-[3px] flex justify-start shrink-0">
          <button
            onClick={toggleSidebar}
            className="bg-[#d4d0c8] text-black px-3 py-0.5 border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] text-[10px] font-bold cursor-pointer"
          >
            ▶ 열기
          </button>
        </div>

        {/* 빈 환자 정보 메시지 */}
        <div className="flex-1 p-4 flex items-center justify-center text-gray-500">
          환자를 선택해주세요
        </div>

        {/* 하단 로그아웃 버튼 */}
        <div className="p-3 border-t border-[#808080] shrink-0 mt-auto bg-[#f0f0f0]">
          <button
            onClick={handleLogout}
            className="w-full bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] text-[#ff0000] font-bold py-2.5 cursor-pointer text-center hover:bg-[#e0e0e0] transition-colors"
          >
            로그아웃 (LOGOUT)
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#f7f7f7] border-r border-[#808080] font-['Gulim'] text-[11px]">
      {/* 1. 상단 열기 바 */}
      <div className="bg-[#000080] p-[3px] flex justify-start shrink-0">
        <button
          onClick={toggleSidebar}
          className="bg-[#d4d0c8] border border-white text-black px-2 py-0.5 cursor-pointer font-bold active:border-inset"
        >
          ▶ 열기
        </button>
      </div>

      {/* 2. 스크롤 영역 (정보 + 테이블) - [수정] p-4, gap-6으로 간격 확대 */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-6">
        {/* 섹션 1: 환자 기본 정보 */}
        <div className="flex flex-col gap-2">
          <div className="bg-[#d4d0c8] border border-[#808080] px-2 py-1.5 font-bold mb-1">
            환자 기본 정보
          </div>

          {/* 이름 박스 여백 증가 */}
          <div className="border border-[#808080] bg-white p-3 mb-2 leading-[1.8]">
            <div>
              성명:{" "}
              <span className="text-[12px] font-bold">{patient.name}</span> (
              {patient.gender === "MALE" ? "남" : "여"}/{patient.monthlyAge}
              개월)
            </div>
          </div>

          {/* 정보 텍스트 줄 간격 확대 (space-y-2) */}
          <div className="space-y-2 pl-1">
            <div>
              <span className="font-bold text-[#555] inline-block w-[70px]">
                생년월일:
              </span>{" "}
              {patient.birthdate}
            </div>
            <div>
              <span className="font-bold text-[#555] inline-block w-[70px]">
                신체정보:
              </span>{" "}
              {patient.height} / {patient.weight}
            </div>
            <div>
              <span className="font-bold text-[#555] inline-block w-[70px]">
                주양육자:
              </span>{" "}
              {patient.caregiver}
            </div>
            <div>
              <span className="font-bold text-[#555] inline-block w-[70px]">
                복용약물:
              </span>{" "}
              {patient.medication}
            </div>
            <div>
              <span className="font-bold text-[#555] inline-block w-[70px]">
                가족력:
              </span>{" "}
              {patient.familyHistory}
            </div>
          </div>
        </div>

        {/* 섹션 2: 과거 병력 (History) */}
        <div className="flex flex-col gap-1">
          <div className="bg-[#d4d0c8] border border-[#808080] px-2 py-1.5 font-bold mb-1">
            과거 병력 (History)
          </div>
          <table className="w-full border-collapse bg-white text-[11px]">
            <thead>
              <tr className="bg-[#e2e2e2]">
                {/* 테이블 헤더 패딩 증가 */}
                <th className="border border-[#999] p-2 w-[60px] text-center font-bold">
                  구분
                </th>
                <th className="border border-[#999] p-2 font-bold">
                  상세 내용
                </th>
              </tr>
            </thead>
            <tbody>
              {patient.history.map((item, idx) => (
                <tr key={`hist-${idx}`}>
                  {/* 테이블 셀 패딩 증가 (p-2) */}
                  <td className="border border-[#ccc] p-2 text-center bg-[#f9f9f9]">
                    {item.category}
                  </td>
                  <td className="border border-[#ccc] p-2">{item.content}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 섹션 3: 상세 호소 및 관찰 */}
        <div className="flex flex-col gap-1">
          <div className="bg-[#d4d0c8] border border-[#808080] px-2 py-1.5 font-bold mb-1">
            상세 호소 및 관찰
          </div>
          <table className="w-full border-collapse bg-white text-[11px]">
            <thead>
              <tr className="bg-[#e2e2e2]">
                <th className="border border-[#999] p-2 w-[60px] text-center font-bold">
                  분류
                </th>
                <th className="border border-[#999] p-2 font-bold">
                  관찰 내용
                </th>
              </tr>
            </thead>
            <tbody>
              {patient.complaints.map((item, idx) => (
                <tr key={`comp-${idx}`}>
                  <td className="border border-[#ccc] p-2 text-center bg-[#f9f9f9]">
                    {item.category}
                  </td>
                  <td className="border border-[#ccc] p-2">{item.content}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. 하단 로그아웃 버튼 (고정) */}
      <div className="p-3 border-t border-[#808080] shrink-0 mt-auto bg-[#f0f0f0]">
        <button
          onClick={handleLogout}
          className="w-full bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] text-[#ff0000] font-bold py-2.5 cursor-pointer text-center hover:bg-[#e0e0e0] transition-colors"
        >
          로그아웃 (LOGOUT)
        </button>
      </div>
    </div>
  );
}
