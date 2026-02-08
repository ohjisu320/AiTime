import { Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface MobileLayoutProps {
  className?: string; // 추가적인 스타일링을 위한 prop 유지
}

const MobileLayout = ({ className }: MobileLayoutProps) => {
  return (
    // Outer Wrapper: 전체 너비 및 배경색 담당 (min-h-screen 필수)
    <div className={cn("w-full min-h-screen flex flex-col items-center", className)}>
      {/* Inner Container: 콘텐츠 너비 제한 및 Safe Area 처리 */}
      <div className={cn(
        "w-full max-w-screen-xl px-4 font-wanted bg-transparent flex-1 w-full flex flex-col",
        "pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)] pr-[env(safe-area-inset-right)]"
      )}>
        <Outlet />
      </div>
    </div>
  );
};

export default MobileLayout;