import { Loader2 } from "lucide-react";

const LoadingSpinner = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] w-full gap-4">
      {/* 1. 스피너 아이콘: animate-spin으로 회전 효과 부여 */}
      <Loader2 className="h-12 w-12 animate-spin text-[#6366F1] opacity-80" />
      
      {/* 2. 로딩 메시지: 부드러운 텍스트 스타일 적용 */}
      <p className="text-gray-500 font-medium animate-pulse">
        데이터를 불러오는 중입니다...
      </p>
    </div>
  );
};

export default LoadingSpinner;