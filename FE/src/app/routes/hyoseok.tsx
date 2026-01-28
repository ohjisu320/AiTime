import type { RouteObject } from "react-router-dom";
import MobileLayout from "@/components/layout/MobileLayout";


//부모
import EditProfilePage from "@/features/auth/pages/EditProfilePage";
import DashboardPage from "@/features/parent/pages/DashboardPage";

import ProfileSelectPage from "@/features/auth/pages/ProfileSelectPage";

//의사
import DoctorDashboard from "@/features/doctor/pages/DoctorDashboard";
import DoctorExamReportPage from "@/features/doctor/pages/DoctorExamReportPage";
import DoctorTaskVideoPage from "@/features/doctor/pages/DoctorTaskVideoPage";

//데스크
import DeskDashboard from "@/features/desk/pages/DeskDashboard";


// 페이지 컴포넌트 (추후 실제 파일 경로로 수정 가능)
// const DashboardPage = () => <div>부모님 대시보드</div>;
// const DoctorDashboard = () => <div>의사 대시보드</div>;

export const hyoseokRoutes: RouteObject[] = [
  // 부모님용 (모바일)
  {
    path: "/parent",
    children: [
      // 프로필 선택 페이지 (MobileLayout 외부)
      // 경로: /parent/select-profile
      { path: "select-profile", element: <ProfileSelectPage /> },

      // 메인 서비스 페이지들 (MobileLayout 내부)
      // 경로: /parent/dashboard, /parent/exam 등
      {
        element: <MobileLayout />,
        children: [
          { path: "dashboard", element: <DashboardPage /> },
          { path: "exam", element: <div>아이 검사 페이지</div> },
          { path: "mypage/edit", element: <EditProfilePage /> },
        ],
      },
    ],
  },
  // 의사용 (데스크탑)
  {
    path: "/doctor",
  
    children: [
      { path: "dashboard", element: <DoctorDashboard /> },
      { path: "patients", element: <div>환자 목록</div> },
      // :id 는 URL 파라미터입니다 (예: /doctor/report/uuid-1)
      { path: "report/:id", element: <DoctorExamReportPage /> },
      { path: "report/:id/videos", element: <DoctorTaskVideoPage /> },
    ],
  },

  // 3. 접수처(데스크)용 ( URL: /reception/dashboard)
  {
    path: "/reception",
    children: [
      { path: "dashboard", element: <DeskDashboard /> },
    ],
  },
];
