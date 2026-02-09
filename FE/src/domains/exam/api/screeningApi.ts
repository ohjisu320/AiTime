// src/domains/exam/api/screeningApi.ts
import api from '@/api/axiosConfig';

// ==================== Type Definitions ====================

export interface ScreeningSessionResponse {
  sessionId: string;
  roomName: string;
  userToken: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'READY' | 'FAILED' | 'TIMEOUT';
  createdAt: string;
}

export interface ScreeningStatusResponse {
  sessionId: string;
  roomName: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'READY' | 'FAILED' | 'TIMEOUT';
  message: string;
}

// AI로부터 수신하는 Data Channel 메시지 타입
export interface ScreeningGuideMessage {
  type: 'guide';
  message: string;
  person_count?: number;
  distance?: number;
  timestamp?: string;
}

export interface ScreeningCompleteMessage {
  type: 'screening_complete';
  status: 'success' | 'failed';
  summary?: {
    total_frames: number;
    valid_frames: number;
    confidence: number;
  };
}

export interface ScreeningErrorMessage {
  type: 'error';
  message: string;
  code: string;
}

export type ScreeningDataMessage =
  | ScreeningGuideMessage
  | ScreeningCompleteMessage
  | ScreeningErrorMessage;

// ==================== API Functions ====================

/**
 * 스크리닝 세션 시작
 * POST /api/v1/screening/start
 */
export const startScreeningSession = async (
  childId: string
): Promise<ScreeningSessionResponse> => {
  console.log('📤 [스크리닝 세션 시작] childId:', childId);

  const { data } = await api.post('/screening/start', { childId });

  console.log('✅ 스크리닝 세션 생성 완료:', data.data);
  return data.data;
};

/**
 * 스크리닝 상태 조회
 * GET /api/v1/screening/status
 */
export const getScreeningStatus = async (): Promise<ScreeningStatusResponse> => {
  console.log('📤 [스크리닝 상태 조회]');

  const { data } = await api.get('/screening/status');

  console.log('✅ 스크리닝 상태:', data.data);
  return data.data;
};

