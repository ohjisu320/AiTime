import { createBrowserRouter } from "react-router-dom";

// 1. 레이아웃 (껍데기)
import MobileLayout from "@/components/layout/MobileLayout";
import DesktopLayout from "@/components/layout/DesktopLayout";

// 2. 페이지 (알맹이)
import LoginPage from "@/features/auth/pages/LoginPage";
import SignupPage from "@/features/auth/pages/SignupPage";
import FindAccountPage from "@/features/auth/pages/FindAccountPage";

const DashboardPage = () => <div>부모님 대시보드</div>;
const DoctorDashboard = () => <div>의사 대시보드</div>;

export const router = createBrowserRouter([
  // 기본 경로 (로그인 화면)
  {
    path: "/",
    element: <LoginPage />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/signup",
    element: <SignupPage />,
  },
  { path: "/find-account", element: <FindAccountPage /> },
  // 부모님용 (모바일)
  {
    path: "/parent",
    element: <MobileLayout />,
    children: [
      { path: "dashboard", element: <DashboardPage /> },
      { path: "exam", element: <div>아이 검사 페이지</div> },
    ],
  },

  // 의사용 (데스크탑)
  {
    path: "/doctor",
    element: <DesktopLayout />,
    children: [
      { path: "dashboard", element: <DoctorDashboard /> },
      { path: "patients", element: <div>환자 목록</div> },
    ],
  },
]);
