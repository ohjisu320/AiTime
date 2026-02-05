// src/domains/exam/constants/missionData.ts 

export const SCREENING_CONTENT: Record<string, any> = {
  "POSE_IMITATION": { // TASK1: 동작 모방
    step: "01",
    engTitle: "Action Imitation",
    korTitle: "동작 모방하기",
    description: '아이에게 특정 동작을 보여주고 따라 하는지 관찰합니다.',
    variant: 'pink',
    duration: 24,
    instructions: [
      { id: 1, text: "아이와 눈을 맞춘 상태에서", boldText: "가슴 높이", suffix: "에서 준비해주세요" },
      { id: 2, text: "정확하게", boldText: "3번 이상", suffix: "박수를 쳐주세요" },
      { id: 3, text: "정확하게", boldText: "3번 이상", suffix: "박수를 쳐주세요" },
      { id: 4, text: "정확하게", boldText: "3번 이상", suffix: "박수를 쳐주세요" },
      { id: 5, text: "정확하게", boldText: "3번 이상", suffix: "박수를 쳐주세요" },
      { id: 6, text: "정확하게", boldText: "3번 이상", suffix: "박수를 쳐주세요" },
    ],
    script: { lines: ["자, 엄마(아빠) 봐봐!", "짝! 짝! 짝!", "우리 ㅇㅇ이도 해볼까?"] }
  },

  // =================================================================
  // TASK 1: 동작 모방 (POSE_IMITATION)
  // [18-23개월] 1. 점프 -> 2. 공 차기 -> 3. 공 던지기
  // =================================================================
  "POSE_IMITATION_18M": {
    step: "01",
    engTitle: "Action Imitation (18-23m)",
    korTitle: "동작 모방",
    description: "점프, 공 차기, 공 던지기 동작을 차례로 보여주고 따라 하는지 관찰합니다.",
    variant: 'pink',
    duration: 24,
    instructions: [
      {
        id: 1,
        text: "무릎을 굽혔다가",
        boldText: "양발을 모아",
        suffix: "쿵 소리가 나게 뛰어주세요 (점프)"
      },
      {
        id: 2,
        text: "멈춰 있는 공을",
        boldText: "발로 힘차게",
        suffix: "뻥 차는 시범을 보여주세요"
      },
      {
        id: 3,
        text: "공을 머리 위로 들어",
        boldText: "앞으로 멀리",
        suffix: "던지는 동작을 보여주세요"
      },
    ],
    script: { lines: ["토끼처럼 깡충!", "공을 발로 뻥~!", "머리 위로 슝~!"] }
  },

  // =================================================================
  // TASK 2: 언어/발화 모방 (SPEECH_IMITATION)
  // [12-17개월] 자극: 아, 마, 바, 맘마, 까꿍
  // 총 15단계 (5개 단어 * 3회 반복)
  // =================================================================
  "SPEECH_IMITATION_12M": {
    step: "02",
    engTitle: "Vocal Imitation",
    korTitle: "발화 모방 자극",
    description: '단어나 소리를 들려주고 아이가 따라 말하는지 관찰합니다.',
    variant: 'amber',
    duration: 40, // 8초 * 5회 = 40초
    instructions: [
      { id: 1, text: "화면에 보이는 자극을", boldText: "한 번만", suffix: "말해주세요" },
      { id: 2, text: "아이의 첫 발화까지", boldText: "3~5초간", suffix: "조용히 기다려주세요" },
      { id: 3, text: "아이의 첫 발화까지", boldText: "3~5초간", suffix: "조용히 기다려주세요" },
      { id: 4, text: "아이의 첫 발화까지", boldText: "3~5초간", suffix: "조용히 기다려주세요" },
      { id: 5, text: "아이의 첫 발화까지", boldText: "3~5초간", suffix: "조용히 기다려주세요" },
    ],
    script: { lines: ["좋아요. 화면에 보이는", "자극(예: 맘마, 까꿍)을", "한 번만 말해 주세요."] }
  },
  "NAME_NON_FACING": { // TASK3: 비대면 호명 반응
    step: "03",
    engTitle: "Name Response (Offline)",
    korTitle: "비대면 호명 반응",
    description: '시야 밖에서 이름을 불렀을 때 고개를 돌려 반응하는지 확인합니다.',
    variant: 'violet',
    duration: 48, // 8초 * 6회 = 48초
    instructions: [
      { id: 1, text: "아이의 등 뒤나", boldText: "시야 밖 사각지대", suffix: "로 이동해주세요" },
      { id: 2, text: "신체 접촉 없이", boldText: "이름만", suffix: "명확하게 불러주세요" },
      { id: 3, text: "신체 접촉 없이", boldText: "이름만", suffix: "명확하게 불러주세요" },
      { id: 4, text: "신체 접촉 없이", boldText: "이름만", suffix: "명확하게 불러주세요" },
      { id: 5, text: "신체 접촉 없이", boldText: "이름만", suffix: "명확하게 불러주세요" },
      { id: 6, text: "신체 접촉 없이", boldText: "이름만", suffix: "명확하게 불러주세요" },
    ],
    script: { lines: ["평소 목소리 톤으로", "아이의 이름을", "ㅇㅇ아! 라고 불러주세요"] }
  },
  "NAME_FACING": { // TASK4: 대면 호명 반응
    step: "04",
    engTitle: "Name Response (Visual)",
    korTitle: "대면 호명 반응",
    description: '마주 본 상태에서 이름을 불렀을 때 눈을 맞추는지 확인합니다.',
    variant: 'emerald',
    duration: 24, // 8초 * 3회 = 24초
    instructions: [
      { id: 1, text: "아이와 부모님이", boldText: "화면 중앙", suffix: "에 들어오게 해주세요" },
      { id: 2, text: "아이가 부모님과", boldText: "마주보게", suffix: "한 뒤 이름을 불러주세요" },
      { id: 3, text: "아이가 부모님과", boldText: "마주보게", suffix: "한 뒤 이름을 불러주세요" },
    ],
    script: { lines: ["아이의 이름을 부르고", "눈을 맞추는지", "잠깐 기다리며 확인해주세요"] }
  }
};

export const VIDEO_TYPE_MAP: Record<string, string> = {
  'POSE_IMITATION': 'TASK1',
  'SPEECH_IMITATION': 'TASK2',
  'NAME_FACING': 'TASK3',
  'NAME_NON_FACING': 'TASK4'
};

export const CLIENT_TO_SERVER_VIDEO_TYPE_MAP: Record<string, string> = {
  'TASK1': 'POSE_IMITATION',
  'TASK2': 'SPEECH_IMITATION',
  'TASK3': 'NAME_FACING',
  'TASK4': 'NAME_NON_FACING',
  '1': 'POSE_IMITATION',
  '2': 'SPEECH_IMITATION',
  '3': 'NAME_FACING',
  '4': 'NAME_NON_FACING',
  // Identity Mappings (이미 올바른 타입인 경우)
  'POSE_IMITATION': 'POSE_IMITATION',
  'SPEECH_IMITATION': 'SPEECH_IMITATION',
  'NAME_FACING': 'NAME_FACING',
  'NAME_NON_FACING': 'NAME_NON_FACING'
};