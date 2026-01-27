import React from "react";
import { Search, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface FilterState {
  name: string;
  birthDate: string;
  phone: string;
  [key: string]: string; // 추가 필드 허용
}

interface SearchBarProps {
  filters: FilterState;
  onFilterChange: (key: string, value: string) => void;
  onSearch: () => void;
  onReset: () => void;
  children?: React.ReactNode; // 추가 필드(예: Select)를 위한 슬롯
}

export default function SearchBar({
  filters,
  onFilterChange,
  onSearch,
  onReset,
  children,
}: SearchBarProps) {
  // 엔터키 입력 시 검색 트리거
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") onSearch();
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-wrap items-center gap-4 mb-6 shadow-sm">
      {/* 공통 필드: 이름 */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-bold text-gray-600 shrink-0">환자명</span>
        <Input
          placeholder="김누구"
          className="w-32 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
          value={filters.name}
          onChange={(e) => onFilterChange("name", e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>

      {/* 공통 필드: 생년월일 */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-bold text-gray-600 shrink-0">
          생년월일
        </span>
        <Input
          placeholder="2026.01.01"
          className="w-36 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
          value={filters.birthDate}
          onChange={(e) => onFilterChange("birthDate", e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>

      {/* 공통 필드: 전화번호 */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-bold text-gray-600 shrink-0">
          보호자 전화번호
        </span>
        <Input
          placeholder="010-1234-5678"
          className="w-40 h-10 bg-gray-50 border-gray-200 focus-visible:ring-[#5A55D6]"
          value={filters.phone}
          onChange={(e) => onFilterChange("phone", e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>

      {/* 추가 필드 영역 (의사용 Select 등) */}
      {children}

      {/* 버튼 그룹 */}
      <div className="ml-auto flex gap-2">
        <Button
          variant="outline"
          onClick={onReset}
          className="h-10 px-4 text-sm font-bold text-gray-600 border-gray-300 hover:bg-gray-50"
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          초기화
        </Button>
        <Button
          onClick={onSearch}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800 h-10 px-6 text-sm font-bold shadow-sm transition-colors"
        >
          <Search className="w-4 h-4 mr-2" />
          검색하기
        </Button>
      </div>
    </div>
  );
}
