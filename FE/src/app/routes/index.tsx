import { createBrowserRouter } from "react-router-dom";
import { hyoseokRoutes } from "./hyoseok";
import { jisuRoutes } from "./jisu";

// 공통 페이지 (로그인 관련)
import LoginPage from "@/features/auth/pages/LoginPage";
import SignupPage from "@/features/auth/pages/SignupPage";
import FindAccountPage from "@/features/auth/pages/FindAccountPage";

export const router = createBrowserRouter([
  // 1. 공통 및 인증 경로
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
  
  // 2. 팀원별 경로 합치기
  ...hyoseokRoutes,
  ...jisuRoutes,
]);