// src/features/exam/api/screeningApi.ts
export const sendSdpOffer = async (sdp: string, type: string) => {
  const response = await fetch('/api/offer', { // 환경에 맞게 엔드포인트 수정
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sdp, type }),
  });

  if (!response.ok) throw new Error('WebRTC 시그널링 실패');
  return response.json();
};