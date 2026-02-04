import { useState, useEffect } from 'react';
import { getExamInfo, type VideoTask as ServerVideoTask } from '../api/examApi';
import type { Mission } from '../types/mission';

// ----------------------------------------------------------------------
// 1. UI 전용 메타 데이터 (고정 정보 - 타이틀, 색상 등)
// ----------------------------------------------------------------------
const MISSION_UI_META: Record<string, any> = {
  POSE_IMITATION: {
    title: '동작 모방하기',
    subTitle: 'Motion Imitation',
    description: '아이에게 특정 동작을 보여주고 따라 하는지 관찰합니다.',
    variant: 'pink',
  },
  SPEECH_IMITATION: {
    title: '발화 모방 자극',
    subTitle: 'Verbal Imitation',
    description: '단어나 소리를 들려주고 아이가 따라 말하는지 관찰합니다.',
    variant: 'amber',
  },
  NAME_FACING: {
    title: '대면 호명반응',
    subTitle: 'Face-to-Face Name Call',
    description: '마주 본 상태에서 이름을 불렀을 때 눈을 맞추는지 확인합니다.',
    variant: 'emerald',
  },
  NAME_NON_FACING: {
    title: '비대면 호명반응',
    subTitle: 'Non-Face Name Call',
    description: '시야 밖에서 이름을 불렀을 때 고개를 돌려 반응하는지 확인합니다.',
    variant: 'violet',
  },
};

// ----------------------------------------------------------------------
// 2. 월령별/미션별 상세 가이드 데이터 (동적 정보 - 스크립트, 가이드)
// ----------------------------------------------------------------------
const MISSION_DETAIL_BY_AGE: Record<string, { '12-17': any; '18-23': any; common?: any }> = {
  POSE_IMITATION: {
    '12-17': {
      steps: [
        {
          title: '손뼉 치기',
          guide: '아이와 눈을 맞춘 상태에서, 가슴 높이에서 크고 정확하게 3번 이상 박수를 쳐주세요.',
          script: '자, 엄마(아빠) 봐봐! 짝! 짝! 짝! 우리 ㅇㅇ이도 해볼까?',
        },
        {
          title: '만세 동작',
          guide: '양팔을 머리 위로 쭉 뻗어 올리며, 활짝 펴는 모습을 보여주세요.',
          script: '우리 만세 해볼까? 자~ 높이높이 만세!!',
        },
        {
          title: '뒷걸음질',
          guide: '아이를 바라보고 서서, 뒤로 3~4걸음 천천히 물러나는 모습을 보여주세요.',
          script: '엄마(아빠)처럼 뒤로 가볼까? 엉금~ 엉금~ 뒤로 가보자!',
        },
      ],
    },
    '18-23': {
      steps: [
        {
          title: '제자리 깡충 뛰기',
          guide: "무릎을 살짝 굽혔다가, 양발을 모아 '쿵' 소리가 나도록 뛰는 모습을 보여주세요.",
          script: '토끼처럼 깡충! 점프! ㅇㅇ이도 같이 점프해 볼까?',
        },
        {
          title: '공 발로 차기',
          guide: "멈춰 있는 공을 발로 힘차게 '뻥' 차는 시범을 보여주세요. (공이 없으면 시늉 가능)",
          script: '여기 공이 있네? 발로 뻥~! 차보자. 뻥!',
        },
        {
          title: '머리 위로 공 던지기',
          guide: '공을 머리 위로 들어 올려, 앞으로 멀리 던지는 동작을 보여주세요. (오버핸드)',
          script: '공을 머리 위로 슝~! 던져보자. 하나, 둘, 셋, 슝~!',
        },
      ],
    },
  },
  SPEECH_IMITATION: {
    '12-17': {
      words: ['아', '마, 바', '맘마', '까꿍'],
      steps: [], // 발화 모방은 words 위주
    },
    '18-23': {
      words: ['엄마, 우유', '자동차', '여기 봐', '야호!'],
      steps: [],
    },
    common: {
      guideLines: [
        '화면에 보이는 자극을 한 번만 말해 주세요.',
        '아이의 첫 발화까지 걸린 시간과, 모방이 되었는지를 기록하고 있어요.',
        '같은 자극으로 총 3회 시도합니다.',
      ],
    },
  },
  NAME_FACING: {
    '12-17': { steps: [] },
    '18-23': { steps: [] },
    common: {
      steps: [
        {
          title: '준비 및 호명',
          guide: '부모님과 아이 얼굴이 모두 화면 중앙에 들어오도록, 아이가 부모님을 마주보게 해주세요.',
          script: '지금 아이 이름을 한 번만 불러주세요. 예: "OO아"',
        },
      ],
    },
  },
  NAME_NON_FACING: {
    '12-17': { steps: [] },
    '18-23': { steps: [] },
    common: {
      steps: [
        {
          title: '이름 부르기 (시도 1)',
          guide: '아이의 시야 밖(뒤/옆 1~2m)에서 평소 목소리로 이름을 명확하게 불러주세요.',
          script: 'ㅇㅇ아!',
        },
        {
          title: '재시도 (시도 2)',
          guide: '5초 내 반응이 없다면, 조금 더 크고 높은 톤으로 불러보세요.',
          script: 'ㅇㅇ아!',
        },
        {
          title: '재재시도 (시도 3)',
          guide: '5초 내 반응이 없다면, 애칭을 섞어 다시 한번 불러보세요.',
          script: '우리 ㅇㅇ이! 또는 ㅇㅇ아, 여기 봐!',
        },
      ],
    },
  },
};

// ----------------------------------------------------------------------
// 3. Hook 구현
// ----------------------------------------------------------------------
export const useMissions = (examId?: string) => {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUnder18, setIsUnder18] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {

    // ✅ childId 또는 selectedChildId 확인 (프로필 선택 시 selectedChildId로 저장됨)
    const childId = localStorage.getItem('selectedChildId');



    const fetchAllData = async () => {
      try {
        setIsLoading(true); // 로딩 시작 명시
        setError(null);
        if (!childId) throw new Error("Child Check Failed");

        // ✅ 실제 API 호출 (getExamInfo 사용)
        const examInfo = await getExamInfo(childId as string);

        const { under18, videoTasks } = examInfo;

        // 1. 월령 그룹 결정
        const ageGroupKey = under18 ? '12-17' : '18-23';
        setIsUnder18(under18);

        // 2. 서버 데이터 매핑
        const mergedMissions: Mission[] = videoTasks.map((task: ServerVideoTask) => {
          // 서버 타입(POSE_IMITATION 등)을 그대로 UI 타입으로 사용
          const uiVideoType = task.videoType;

          const uiMeta = MISSION_UI_META[uiVideoType] || {};
          const detailMeta = MISSION_DETAIL_BY_AGE[uiVideoType] || {};

          let ageSpecificDetail = detailMeta[ageGroupKey] || {};
          if (detailMeta.common) {
            ageSpecificDetail = { ...ageSpecificDetail, ...detailMeta.common };
          }


          // ✅ 월령별 분기 처리 (SCREENING_CONTENT 매핑용)
          let resolvedVideoType: string = uiVideoType;
          if (['POSE_IMITATION', 'SPEECH_IMITATION'].includes(uiVideoType)) {
            resolvedVideoType = `${uiVideoType}${under18 ? '_12M' : '_18M'}`;
          }

          return {
            ...task,
            ...uiMeta,
            detail: ageSpecificDetail,
            type: resolvedVideoType,
            videoType: resolvedVideoType,
            originalVideoType: task.videoType
          } as Mission;
        });

        // 정렬 순서 정의
        const order = ['POSE_IMITATION', 'SPEECH_IMITATION', 'NAME_FACING', 'NAME_NON_FACING'];
        mergedMissions.sort((a, b) => order.indexOf(a.originalVideoType || '') - order.indexOf(b.originalVideoType || ''));

        setMissions(mergedMissions);

      } catch (err) {
        console.error("데이터 조회 중 오류 발생:", err);
        setError("데이터를 불러오는 중 오류가 발생했습니다.");
        setMissions([]);

      } finally {
        setIsLoading(false);
      }
    };

    fetchAllData();
  }, [examId]);

  return { missions, isLoading, isUnder18, error };
};