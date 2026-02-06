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
            className="relative w-full h-[500px] md:h-[400px] lg:h-[350px] xl:h-80 bg-gradient-to-r from-[#6366F1] to-[#4F46E5] rounded-3xl shadow-2xl overflow-hidden p-16 flex items-center gap-12 cursor-pointer transition-all hover:brightness-110 active:scale-[0.99]"
        >
            {/* 배경 장식 패턴 */}
            <div className="absolute inset-0 opacity-10 pointer-events-none">
                <div className="absolute w-80 h-80 -right-20 -top-20 bg-white rounded-full blur-3xl" />
                <div className="absolute w-64 h-64 -left-20 top-20 bg-white rounded-full blur-3xl" />
            </div>

            {/* 아이콘 영역 */}
            <div className="relative z-10 w-32 h-32 bg-white rounded-full flex items-center justify-center shrink-0 shadow-xl">
                <Play className="w-14 h-14 text-[#6366F1] fill-[#6366F1] ml-1" />
            </div>

            {/* 텍스트 컨텐츠 영역 */}
            <div className="relative z-10 flex flex-col gap-8 text-white">
                <div className="space-y-2">
                    <h1 className="text-5xl md:text-4xl lg:text-4xl xl:text-4xl font-bold tracking-tight">
                        {title}
                    </h1>
                    <p className="text-white/90 text-2xl md:text-xl lg:text-xl xl:text-xl font-medium">
                        {subtitle}
                    </p>
                </div>

                {/* 버튼 텍스트 */}
                <div className="flex items-center gap-2 text-white/70 text-base font-medium">
                    <span className="bg-white/20 px-4 py-2 rounded-full text-white text-base font-semibold backdrop-blur-sm">
                        {buttonText}
                    </span>
                </div>
            </div>
        </section>
    );
};

export default HeroBanner;
