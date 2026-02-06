// src/features/doctor/components/panels/PatientDetailPanel.tsx
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
    } catch (e) { console.error(e); }
    localStorage.clear();
    navigate("/login");
  };

  if (!patient) {
    return (
      <div className="flex flex-col h-full bg-[#f7f7f7] font-['Gulim'] text-[11px]">
        <div className="bg-[#000080] p-[2px]">
          <button onClick={toggleSidebar} className="windows-btn">▶ 목록 열기</button>
        </div>
        <div className="flex-1 flex items-center justify-center text-gray-400">
          좌측 상단 [▶ 목록 열기]를 눌러<br />환자를 선택해주세요.
        </div>
        <div className="p-2 bg-[#d4d0c8]">
          <button onClick={handleLogout} className="w-full font-bold text-red-600 windows-btn">로그아웃</button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#f7f7f7] font-['Gulim'] text-[11px]">
      <div className="bg-[#000080] p-[2px] shrink-0">
        <button onClick={toggleSidebar} className="windows-btn">▶ 다른 환자 선택</button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* 기본 정보 */}
        <div>
          <div className="windows-header mb-1">환자 기본 정보</div>
          <div className="bg-white border inset-border p-2 space-y-1">
            <div className="font-bold text-[12px] border-b pb-1 mb-1">
              {patient.name} ({patient.gender === "MALE" ? "남" : "여"}, {patient.monthlyAge}개월)
            </div>
            <div><span className="font-bold w-12 inline-block">생년월일:</span> {patient.birthdate}</div>
            <div><span className="font-bold w-12 inline-block">신체:</span> {patient.height} / {patient.weight}</div>
            <div><span className="font-bold w-12 inline-block">보호자:</span> {patient.caregiver}</div>
          </div>
        </div>

        {/* 병력 */}
        <div>
          <div className="windows-header mb-1">과거 병력</div>
          <table className="w-full border-collapse border border-gray-400 bg-white">
            <tbody>
              {patient.history.map((h, i) => (
                <tr key={i} className="border-b border-gray-200">
                  <td className="bg-gray-100 p-1 w-14 text-center border-r font-bold">{h.category}</td>
                  <td className="p-1">{h.content}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 주호소 */}
        <div>
          <div className="windows-header mb-1">주호소 및 관찰</div>
          <ul className="list-disc list-inside bg-white border inset-border p-2 space-y-1">
            {patient.complaints.map((c, i) => (
              <li key={i}>
                <span className="font-bold">[{c.category}]</span> {c.content}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="p-2 bg-[#d4d0c8] shrink-0 border-t border-white">
        <button onClick={handleLogout} className="w-full font-bold text-red-600 windows-btn py-1">
          로그아웃 (EXIT)
        </button>
      </div>

      <style>{`
        .windows-btn {
          background: #d4d0c8;
          border-top: 2px solid white;
          border-left: 2px solid white;
          border-right: 2px solid #404040;
          border-bottom: 2px solid #404040;
          padding: 2px 8px;
          font-weight: bold;
          font-size: 11px;
        }
        .windows-btn:active {
          border-top: 2px solid #404040;
          border-left: 2px solid #404040;
          border-right: 2px solid white;
          border-bottom: 2px solid white;
        }
        .windows-header {
          background: linear-gradient(90deg, #000080, #1084d0);
          color: white;
          padding: 2px 4px;
          font-weight: bold;
        }
        .inset-border {
          border: 2px solid;
          border-color: #808080 white white #808080;
        }
      `}</style>
    </div>
  );
}