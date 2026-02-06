import { createBrowserRouter } from "react-router-dom";
import { hyoseokRoutes } from "./hyoseok";
import { jisuRoutes } from "./jisu";
import GlobalErrorPage from "@/components/common/GlobalErrorPage";

// 공통 페이지 (로그인 관련)
import LoginPage from "@/features/auth/pages/LoginPage";
import StaffLoginPage from "@/features/auth/pages/StaffLoginPage";
import SignupPage from "@/features/auth/pages/SignupPage";
import FindAccountPage from "@/features/auth/pages/FindAccountPage";

export const router = createBrowserRouter([
  // 1. 공통 및 인증 경로
  {
    path: "/",
    element: <LoginPage />,
    errorElement: <GlobalErrorPage />, // ✅ 루트 레벨 에러 핸들링
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/staff-login",
    element: <StaffLoginPage />,
  },
  {
    path: "/signup",
    element: <SignupPage />,
  },
  { path: "/find-account", element: <FindAccountPage /> },

  // 2. 팀원별 경로 합치기
  ...hyoseokRoutes,
  ...jisuRoutes,

  // 3. 404 Catch-all Route (모든 정의되지 않은 경로)
  {
    path: "*",
    element: <GlobalErrorPage />,
  },
]);