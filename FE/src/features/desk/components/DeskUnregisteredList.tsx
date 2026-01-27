import { Mail, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import StatusBadge from "@/components/common/StatusBadge";
import EmptyState from "@/components/common/EmptyState";

// 데이터 타입 정의
export interface InviteCodePatientItem {
  inviteCodeId: string;
  childName: string;
  childMonths: number;
  parentPhone: string;
  scheduledAt: string;
  status: "ISSUED" | "REGISTERED" | "EXPIRED" | "REVOKED";
  inviteCode: string;
}

interface DeskUnregisteredListProps {
  patients: InviteCodePatientItem[];
  selectedIds: Set<string>;
  onSelectAll: (checked: boolean) => void;
  onSelectOne: (id: string) => void;
  onDelete: (id: string) => void;
  emptyMessage: string;
  dateLabel?: string;
}

export default function DeskUnregisteredList({
  patients,
  selectedIds,
  onSelectAll,
  onSelectOne,
  onDelete,
  emptyMessage,
  dateLabel,
}: DeskUnregisteredListProps) {
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
        <div className="w-[15%]">환자 정보</div>
        <div className="w-[10%] text-center">나이</div>
        <div className="w-[15%] text-center">예약일</div>
        <div className="w-[20%] text-center">초대코드 상태</div>
        <div className="w-[15%] text-center">초대코드</div>
        <div className="w-[20%] text-right">관리</div>
      </div>

      {/* 리스트 */}
      <div className="divide-y divide-gray-100">
        {patients.length > 0 ? (
          patients.map((patient) => (
            <div
              key={patient.inviteCodeId}
              className="flex items-center px-6 py-5 hover:bg-gray-50/50 transition-colors"
            >
              <div className="w-[5%]">
                <Checkbox
                  checked={selectedIds.has(patient.inviteCodeId)}
                  onCheckedChange={() => onSelectOne(patient.inviteCodeId)}
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
                <StatusBadge
                  status={patient.status}
                  label={
                    patient.status === "ISSUED"
                      ? "미등록"
                      : patient.status === "REVOKED"
                        ? "취소됨"
                        : "등록완료"
                  }
                />
              </div>
              <div className="w-[15%] text-center text-sm font-mono text-gray-600">
                {patient.inviteCode}
              </div>
              <div className="w-[20%] flex justify-end gap-2 items-center">
                <Button className="bg-sky-500 hover:bg-sky-600 h-8 px-3 text-xs font-bold text-white gap-1">
                  <Mail className="w-3 h-3" /> 재전송
                </Button>
                <button
                  onClick={() => onDelete(patient.inviteCodeId)}
                  className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
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
