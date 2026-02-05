import { Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface MobileLayoutProps {
  className?: string; // 추가적인 스타일링을 위한 prop 유지
}

const MobileLayout = ({ className }: MobileLayoutProps) => {
  return (
    // 1600px 최적화, 반응형 너비, 중앙 정렬, 유연한 배경색
    <div className={cn("w-full max-w-[1600px] mx-auto px-4 bg-background/0 font-wanted", className)}>
      <Outlet />
    </div>
  );
};

export default MobileLayout;