import type { RouteObject } from 'react-router-dom';
import { lazy } from 'react';

const MissionListPage = lazy(() => import('@/domains/exam/pages/MissionListPage'));

export const jisuRoutes: RouteObject[] = [
  {
    path: "/exam",
    children: [
      { path: "mission", element: <MissionListPage /> }, // 태스크리스트 페이지
    ],
  },
];