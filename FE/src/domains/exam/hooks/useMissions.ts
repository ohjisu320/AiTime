import { useState, useEffect } from 'react';
import { fetchMissionList } from '../api/missionApi';

// 💡 서버 연동 시 false로 변경하세요! 
const USE_MOCK = true; 

// UI 전용 데이터 (서버에서 내려주지 않는 고정 정보) 
const MISSION_UI_META: Record<string, any> = {
  TASK1: { title: '이름 부르기 반응', subTitle: 'Name Response', description: '아이의 이름을 불러 눈맞춤과 반응을 관찰합니다', variant: 'pink' },
  TASK2: { title: '사물 가리키기', subTitle: 'Object Pointing', description: '"공 어디 있어?" 같은 질문에 가리키는 행동을 관찰합니다', variant: 'amber' },
  TASK3: { title: '간단한 지시 따르기', subTitle: 'Simple Commands', description: '"공 가져와", "앉아" 같은 간단한 지시를 따르는지 관찰합니다', variant: 'emerald' },
  TASK4: { title: '자유 놀이 관찰', subTitle: 'Free Play', description: '장난감과 자유롭게 놀 때의 행동 패턴을 관찰합니다', variant: 'violet' },
};

export const useMissions = () => {
  const [missions, setMissions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const getMissions = async () => {
      try {
        let serverTasks = [];
        
        if (USE_MOCK) {
          // 테스트용 Mock 데이터 
          serverTasks = [
            { videoType: 'TASK1', status: 'UPLOADED' },
            { videoType: 'TASK2', status: 'PENDING' },
            { videoType: 'TASK3', status: 'PENDING' },
            { videoType: 'TASK4', status: 'UPLOADED' },
          ];
        } else {
          serverTasks = await fetchMissionList();
        }

        // ✅ 서버의 상태 데이터와 프론트의 UI 정보를 병합합니다. 
        const mergedMissions = serverTasks.map((task: any) => ({
          ...task,
          ...MISSION_UI_META[task.videoType],
          type: task.videoType, // MissionCard 컴포넌트 호환용 
        }));

        setMissions(mergedMissions);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    getMissions();
  }, []);

  return { missions, isLoading };
};