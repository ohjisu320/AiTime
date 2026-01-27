// API 명세의 공통 응답 구조를 반영합니다. 
export const fetchMissionList = async () => {
  // 실제 엔드포인트 예시: /api/v1/exam/progress
  const response = await fetch('/api/v1/exam/progress'); 
  const result = await response.json();
  
  if (result.code === 200 && result.data) {
    return result.data.videoTasks; // TASK 리스트 배열만 반환 
  }
  
  throw new Error(result.message || '검사 진행도를 불러오지 못했습니다.');
};