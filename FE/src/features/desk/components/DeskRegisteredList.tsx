import { Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import StatusBadge from "@/components/common/StatusBadge";
import EmptyState from "@/components/common/EmptyState";

// 데이터 타입 정의
export interface ReservationChildItem {
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

interface DeskRegisteredListProps {
  patients: ReservationChildItem[];
  selectedIds: Set<string>;
  onSelectAll: (checked: boolean) => void;
  onSelectOne: (id: string) => void;
  emptyMessage: string;
  dateLabel?: string;
}

export default function DeskRegisteredList({
  patients,
  selectedIds,
  onSelectAll,
  onSelectOne,
  emptyMessage,
  dateLabel,
}: DeskRegisteredListProps) {
  const isAllSelected =
    patients.length > 0 && patients.length === selectedIds.size;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center bg-gray-50 px-6 py-4 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-wider">
        <div className="w-[5%]">
          <Checkbox
            checked={isAllSelected}
            onCheckedChange={(c) => onSelectAll(!!c)}
          />
        </div>
        <div className="w-[20%]">환자 정보</div>
        <div className="w-[10%] text-center">나이</div>
        <div className="w-[20%] text-center">예약일</div>
        <div className="w-[15%] text-center">검사 상태</div>
        <div className="w-[30%] text-right">안내 메시지</div>
      </div>

      {/* 리스트 */}
      <div className="divide-y divide-gray-100">
        {patients.length > 0 ? (
          patients.map((patient) => (
            <div
              key={patient.hospitalChildrenId}
              className="flex items-center px-6 py-5 hover:bg-gray-50/50 transition-colors"
            >
              <div className="w-[5%]">
                <Checkbox
                  checked={selectedIds.has(patient.hospitalChildrenId)}
                  onCheckedChange={() =>
                    onSelectOne(patient.hospitalChildrenId)
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
                <StatusBadge
                  status={patient.examStatus}
                  label={patient.examStatus === "COMPLETED" ? "완료" : "미완료"}
                />
              </div>
              <div className="w-[30%] flex justify-end gap-2">
                <Button className="bg-sky-500 hover:bg-sky-600 text-white h-8 px-4 text-xs font-bold gap-1">
                  <Mail className="w-3 h-3" /> 전송
                </Button>
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
