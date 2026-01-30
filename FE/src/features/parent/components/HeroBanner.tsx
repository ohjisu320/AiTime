import { Play } from 'lucide-react';
import type { HeroBannerProps } from '../hooks/useDashboardLogic'; // Import type from hook

const HeroBanner = ({ title, subtitle, buttonText, status, onPrimaryAction }: HeroBannerProps) => {
  return (
    <section
      onClick={onPrimaryAction} // Use the action passed from prop
      data-status={status} // Pass status to DOM for debugging/styling (fixes unused var)
      className="relative w-full h-80 md:h-72 lg:h-64 xl:h-60 bg-gradient-to-r from-[#6366F1] to-[#4F46E5] rounded-3xl shadow-2xl overflow-hidden p-12 flex items-center gap-8 cursor-pointer transition-all hover:brightness-110 active:scale-[0.99]"
    >
      {/* 배경 장식 패턴 */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        <div className="absolute w-80 h-80 -right-20 -top-20 bg-white rounded-full blur-3xl" />
        <div className="absolute w-64 h-64 -left-20 top-20 bg-white rounded-full blur-3xl" />
      </div>

      {/* 아이콘 영역 */}
      <div className="relative z-10 w-24 h-24 bg-white rounded-full flex items-center justify-center shrink-0 shadow-xl">
        <Play className="w-10 h-10 text-[#6366F1] fill-[#6366F1] ml-1" />
      </div>

      {/* 텍스트 컨텐츠 영역 */}
      <div className="relative z-10 flex flex-col gap-3 text-white">
        <div className="space-y-1">
          <h1 className="text-4xl font-bold tracking-tight">
            {title}
          </h1>
          <p className="text-white/90 text-xl font-medium">
            {subtitle}
          </p>
        </div>

        {/* 버튼 텍스트 표시 (옵션: 실제 버튼처럼 보이게 하거나 텍스트로 유지) */}
        <div className="flex items-center gap-2 text-white/70 text-sm font-medium">
          <span className="bg-white/20 px-3 py-1 rounded-full text-white text-sm font-semibold backdrop-blur-sm">
            {buttonText}
          </span>
        </div>
      </div>
    </section>
  );
};

export default HeroBanner;