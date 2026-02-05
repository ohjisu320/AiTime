import { Outlet } from 'react-router-dom';

const DesktopLayout = () => {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* 사이드바 (임시) */}
      <aside className="w-64 bg-white border-r p-6 hidden md:block">
        <h1 className="text-2xl font-bold mb-8 text-primary">Doctor Admin</h1>
        <nav className="flex flex-col gap-4">
          <div className="p-2 bg-primary/10 text-primary rounded font-bold">대시보드</div>
          <div className="p-2 hover:bg-gray-100 rounded">환자 관리</div>
          <div className="p-2 hover:bg-gray-100 rounded">설정</div>
        </nav>
      </aside>

      {/* 메인 콘텐츠 영역 */}
      <main className="flex-1 p-8 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default DesktopLayout;