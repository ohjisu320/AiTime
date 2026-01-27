import { Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import StatusBadge from "@/components/common/StatusBadge";
import EmptyState from "@/components/common/EmptyState";

// 타입 정의 (필요시 types.ts로 이동 가능)
export interface DoctorPatientItem {
  hospitalChildrenId: string;
  childName: string;
  gender: "MALE" | "FEMALE";
  months: number;
  scheduledAt: string;
  examStatus: "IN_PROGRESS" | "COMPLETED";
  isSubmitted: boolean;
  birthDate?: string;
  parentPhone?: string;
}

interface DoctorPatientListProps {
  patients: DoctorPatientItem[];
  emptyMessage: string;
  dateLabel?: string;
}

export default function DoctorPatientList({
  patients,
  emptyMessage,
  dateLabel,
}: DoctorPatientListProps) {
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    let hour = date.getHours();
    const minute = String(date.getMinutes()).padStart(2, "0");
    const ampm = hour >= 12 ? "오후" : "오전";
    hour = hour % 12 || 12;
    return `${ampm} ${hour}:${minute}`;
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* 테이블 헤더 */}
      <div className="flex items-center bg-gray-50 px-8 py-4 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-wider">
        <div className="w-[20%]">환자 정보</div>
        <div className="w-[15%] text-center">나이</div>
        <div className="w-[25%] text-center">최근 방문 (예약)</div>
        <div className="w-[20%] text-center">상태</div>
        <div className="w-[20%] text-right">액션</div>
      </div>

      {/* 테이블 바디 */}
      <div className="divide-y divide-gray-100">
        {patients.length > 0 ? (
          patients.map((patient) => (
            <div
              key={patient.hospitalChildrenId}
              className="flex items-center px-8 py-5 hover:bg-gray-50/50 transition-colors"
            >
              {/* 환자 정보 */}
              <div className="w-[20%]">
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-[#1A1A1A]">
                    {patient.childName}
                  </span>
                  <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                    {patient.gender === "MALE" ? "남아" : "여아"}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-0.5">
                  ID: {patient.hospitalChildrenId.slice(0, 6)}...
                </div>
              </div>

              {/* 나이 */}
              <div className="w-[15%] text-center text-sm font-medium text-gray-700">
                {patient.months}개월
              </div>

              {/* 방문 일시 */}
              <div className="w-[25%] text-center">
                <div className="text-sm font-medium text-gray-800">
                  {patient.scheduledAt.split("T")[0]}
                </div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {formatTime(patient.scheduledAt)}
                </div>
              </div>

              {/* 상태 */}
              <div className="w-[20%] flex justify-center">
                <StatusBadge
                  status={patient.examStatus}
                  label={
                    patient.examStatus === "COMPLETED" ? "분석완료" : "대기"
                  }
                />
              </div>

              {/* 액션 */}
              <div className="w-[20%] flex justify-end">
                {patient.examStatus === "COMPLETED" ? (
                  <Button className="bg-sky-500 hover:bg-sky-600 text-white h-9 px-4 rounded-lg gap-2 shadow-sm transition-all">
                    <Eye className="w-4 h-4" />
                    <span className="text-xs font-bold">분석 보기</span>
                  </Button>
                ) : (
                  <Button
                    disabled
                    className="bg-gray-400 h-9 px-4 rounded-lg gap-2 text-white opacity-50 cursor-not-allowed"
                  >
                    <Eye className="w-4 h-4" />
                    <span className="text-xs font-bold">분석 대기</span>
                  </Button>
                )}
              </div>
            </div>
          ))
        ) : (
          <EmptyState date={dateLabel} message={emptyMessage} />
        )}
      </div>
    </div>
  );
}
