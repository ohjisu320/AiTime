import React from "react";
import { cn } from "@/lib/utils";

// Windows 98 스타일 컨테이너
export const WindowsContainer = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => (
  <div
    className={cn(
      "bg-white border-2 border-white border-r-[#808080] border-b-[#808080] p-1 overflow-auto",
      className,
    )}
  >
    {children}
  </div>
);

// Windows 98 스타일 버튼
export const WindowsButton = ({ children, onClick, className }: any) => (
  <button
    onClick={onClick}
    className={cn(
      "bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] active:border-t-[#404040] active:border-l-[#404040] px-3 py-1 text-[12px] font-bold cursor-pointer font-['Gulim']",
      className,
    )}
  >
    {children}
  </button>
);

// 섹션 헤더 (제목 크기 증가)
export const SectionHeader = ({
  title,
  children,
}: {
  title: string;
  children?: React.ReactNode;
}) => (
  <div className="flex justify-between items-center bg-[#d4d0c8] border border-[#808080] px-2 py-1.5 mb-1">
    <span className="font-bold text-[#000080] text-[13px]">{title}</span>
    {children}
  </div>
);