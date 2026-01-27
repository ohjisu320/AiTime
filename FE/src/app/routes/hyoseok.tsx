import type { RouteObject } from "react-router-dom";
import MobileLayout from "@/components/layout/MobileLayout";


//페이지
import EditProfilePage from "@/features/auth/pages/EditProfilePage";
import DashboardPage from "@/features/parent/pages/DashboardPage";
import ProfileSelectPage from "@/features/parent/pages/ProfileSelectPage";
import DoctorDashboard from "@/features/doctor/pages/DoctorDashboard";

// 페이지 컴포넌트 (추후 실제 파일 경로로 수정 가능)
// const DashboardPage = () => <div>부모님 대시보드</div>;
// const DoctorDashboard = () => <div>의사 대시보드</div>;

export const hyoseokRoutes: RouteObject[] = [
  // 부모님용 (모바일)
  {
    path: "/parent",
    element: <MobileLayout />,
    children: [
      //parent접속 후 가장 먼저 페이지
      { path: "home", element: <ProfileSelectPage /> },

      { path: "dashboard", element: <DashboardPage /> },
      { path: "exam", element: <div>아이 검사 페이지</div> },

      //회원정보 수정 경로
      { path: "mypage/edit", element: <EditProfilePage /> },
    ],
  },
  // 의사용 (데스크탑)
  {
    path: "/doctor",
  
    children: [
      { path: "dashboard", element: <DoctorDashboard /> },
      { path: "patients", element: <div>환자 목록</div> },
    ],
  },
];
