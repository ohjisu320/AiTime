import { Play } from 'lucide-react';
import type { HeroBannerProps } from '../hooks/useDashboardLogic';

const HeroBanner = ({ title, subtitle, buttonText, status, onPrimaryAction }: HeroBannerProps) => {
    const handleClick = () => {
        console.log('🎯 [HeroBanner] Banner clicked!', { status, title, buttonText });
        console.log('🎯 [HeroBanner] Calling onPrimaryAction...');
        onPrimaryAction();
        console.log('🎯 [HeroBanner] onPrimaryAction called successfully');
    };

    return (
        <section
            onClick={handleClick}
            data-status={status}
            className="relative w-full h-[180px] sm:h-[200px] md:h-[220px] lg:h-[250px] bg-gradient-to-r from-[#6366F1] to-[#4F46E5] rounded-2xl sm:rounded-3xl shadow-2xl overflow-hidden p-6 sm:p-8 md:p-10 lg:p-12 flex items-center gap-4 sm:gap-6 md:gap-8 lg:gap-10 cursor-pointer transition-all hover:brightness-110 active:scale-[0.99]"
        >
            {/* 배경 장식 패턴 */}
            <div className="absolute inset-0 opacity-10 pointer-events-none">
                <div className="absolute w-64 h-64 sm:w-72 sm:h-72 md:w-80 md:h-80 -right-16 sm:-right-20 -top-16 sm:-top-20 bg-white rounded-full blur-3xl" />
                <div className="absolute w-48 h-48 sm:w-56 sm:h-56 md:w-64 md:h-64 -left-16 sm:-left-20 top-16 sm:top-20 bg-white rounded-full blur-3xl" />
            </div>

            {/* 아이콘 영역 */}
            <div className="relative z-10 w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 lg:w-28 lg:h-28 bg-white rounded-full flex items-center justify-center shrink-0 shadow-xl">
                <Play className="w-7 h-7 sm:w-9 sm:h-9 md:w-10 md:h-10 lg:w-12 lg:h-12 text-[#6366F1] fill-[#6366F1] ml-0.5 sm:ml-1" />
            </div>

            {/* 텍스트 컨텐츠 영역 */}
            <div className="relative z-10 flex flex-col gap-3 sm:gap-4 md:gap-5 lg:gap-6 text-white">
                <div className="space-y-1 sm:space-y-1.5 md:space-y-2">
                    <h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold tracking-tight">
                        {title}
                    </h1>
                    <p className="text-white/90 text-sm sm:text-base md:text-lg lg:text-xl font-medium">
                        {subtitle}
                    </p>
                </div>

                {/* 버튼 텍스트 */}
                <div className="flex items-center gap-2 text-white/70 text-xs sm:text-sm md:text-base font-medium">
                    <span className="bg-white/20 px-3 py-1.5 sm:px-4 sm:py-2 rounded-full text-white text-xs sm:text-sm md:text-base font-semibold backdrop-blur-sm">
                        {buttonText}
                    </span>
                </div>
            </div>
        </section>
    );
};

export default HeroBanner;
