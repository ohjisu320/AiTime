import { Outlet } from 'react-router-dom';

const MobileLayout = () => {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 max-w-md mx-auto shadow-xl">
      {/* 헤더 (모바일용 임시) */}
      <header className="h-14 bg-white border-b flex items-center justify-center font-bold text-primary">
        AITIME
      </header>

      {/* 실제 페이지 내용이 들어가는 곳 */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>

      {/* 하단 탭바 (임시) */}
      <nav className="h-16 bg-white border-t flex justify-around items-center text-xs text-gray-500">
        <button>홈</button>
        <button>검사</button>
        <button>내 정보</button>
      </nav>
    </div>
  );
};

export default MobileLayout;