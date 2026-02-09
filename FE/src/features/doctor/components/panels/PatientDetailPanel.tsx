import { useNavigate } from "react-router-dom";
import { logoutHospitalStaff } from "@/features/desk/api/hospitalStaffApi";
import type { PatientDetailFull } from "../../types/doctor";

interface Props {
  patient: PatientDetailFull | null;
  toggleSidebar: () => void;
}

export default function PatientDetailPanel({ patient, toggleSidebar }: Props) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logoutHospitalStaff();
    } catch (error) {
      console.error("로그아웃 API 실패:", error);
    } finally {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
      navigate("/login");
    }
  };

  if (!patient) {
    return (
      <div className="flex flex-col h-full bg-[#f7f7f7] border-r border-[#808080] font-['Gulim'] text-[13px]">
        <div className="bg-[#000080] p-[3px] flex justify-start shrink-0">
          <button
            onClick={toggleSidebar}
            className="bg-[#d4d0c8] text-black px-4 py-1 border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] text-[12px] font-bold cursor-pointer"
          >
            ▶ 열기
          </button>
        </div>
        <div className="flex-1 p-4 flex items-center justify-center text-gray-500 text-[14px]">
          환자를 선택해주세요
        </div>
        <div className="p-3 border-t border-[#808080] shrink-0 mt-auto bg-[#f0f0f0]">
          <button
            onClick={handleLogout}
            className="w-full bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] text-[#ff0000] font-bold py-2.5 cursor-pointer text-center hover:bg-[#e0e0e0] transition-colors text-[13px]"
          >
            로그아웃 (LOGOUT)
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#f7f7f7] border-r border-[#808080] font-['Gulim'] text-[13px]">
      <div className="bg-[#000080] p-[3px] flex justify-start shrink-0">
        <button
          onClick={toggleSidebar}
          className="bg-[#d4d0c8] text-black px-4 py-1 border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] text-[12px] font-bold cursor-pointer"
        >
          ▶ 열기
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <div className="bg-[#d4d0c8] border border-[#808080] px-2 py-2 font-bold mb-1 shadow-sm text-[13px]">
            환자 기본 정보
          </div>

          <div className="border border-[#808080] bg-white p-3 mb-2 leading-[1.8] shadow-sm">
            <div className="text-[14px]">
              성명:{" "}
              <span className="text-[15px] font-bold">{patient.name}</span> (
              {patient.gender === "MALE" ? "남" : "여"}/{patient.monthlyAge}개월)
            </div>
          </div>

          <div className="space-y-2 pl-1 text-[#333] text-[13px]">
            <div><span className="font-bold text-[#000] inline-block w-[80px]">생년월일:</span> {patient.birthdate}</div>
            <div><span className="font-bold text-[#000] inline-block w-[80px]">신체정보:</span> {patient.height} / {patient.weight}</div>
            <div><span className="font-bold text-[#000] inline-block w-[80px]">주양육자:</span> {patient.caregiver}</div>
            <div><span className="font-bold text-[#000] inline-block w-[80px]">복용약물:</span> {patient.medication}</div>
            <div><span className="font-bold text-[#000] inline-block w-[80px]">가족력:</span> {patient.familyHistory}</div>
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="bg-[#d4d0c8] border border-[#808080] px-2 py-2 font-bold mb-1 shadow-sm text-[13px]">
            과거 병력 (History)
          </div>
          <table className="w-full border-collapse bg-white text-[13px] shadow-sm">
            <thead>
              <tr className="bg-[#e2e2e2]">
                <th className="border border-[#999] p-2 w-[80px] text-center font-bold">구분</th>
                <th className="border border-[#999] p-2 font-bold">상세 내용</th>
              </tr>
            </thead>
            <tbody>
              {patient.history.map((item, idx) => (
                <tr key={`hist-${idx}`}>
                  <td className="border border-[#ccc] p-2 text-center bg-[#f9f9f9] font-bold text-[#555]">{item.category}</td>
                  <td className="border border-[#ccc] p-2">{item.content}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-col gap-1">
          <div className="bg-[#d4d0c8] border border-[#808080] px-2 py-2 font-bold mb-1 shadow-sm text-[13px]">
            상세 호소 및 관찰
          </div>
          <table className="w-full border-collapse bg-white text-[13px] shadow-sm">
            <thead>
              <tr className="bg-[#e2e2e2]">
                <th className="border border-[#999] p-2 w-[80px] text-center font-bold">분류</th>
                <th className="border border-[#999] p-2 font-bold">관찰 내용</th>
              </tr>
            </thead>
            <tbody>
              {patient.complaints.map((item, idx) => (
                <tr key={`comp-${idx}`}>
                  <td className="border border-[#ccc] p-2 text-center bg-[#f9f9f9] font-bold text-[#555]">{item.category}</td>
                  <td className="border border-[#ccc] p-2">{item.content}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="p-3 border-t border-[#808080] shrink-0 mt-auto bg-[#f0f0f0]">
        <button
          onClick={handleLogout}
          className="w-full bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] text-[#ff0000] font-bold py-2.5 cursor-pointer text-center hover:bg-[#e0e0e0] transition-colors text-[13px]"
        >
          로그아웃 (LOGOUT)
        </button>
      </div>
    </div>
  );
}