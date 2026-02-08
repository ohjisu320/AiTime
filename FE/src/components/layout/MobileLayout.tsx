import { Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface MobileLayoutProps {
  className?: string; // 추가적인 스타일링을 위한 prop 유지
}

const MobileLayout = ({ className }: MobileLayoutProps) => {
  return (
    // 1180px 너비 최적화, 반응형, 중앙 정렬
    <div className={cn("w-full max-w-screen-xl mx-auto px-4 bg-background/0 font-wanted pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)] pr-[env(safe-area-inset-right)]", className)}>
      <Outlet />
    </div>
  );
};

export default MobileLayout;