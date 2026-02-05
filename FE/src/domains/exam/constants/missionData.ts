// src/domains/exam/constants/missionData.ts

export const SCREENING_CONTENT: Record<string, any> = {
  // =================================================================
  // TASK 1: 동작 모방 (POSE_IMITATION)
  // [12-17개월] 1. 손뼉 -> 2. 만세 -> 3. 뒷걸음질
  // =================================================================
  "POSE_IMITATION_12M": {
    step: "01",
    engTitle: "Action Imitation (12-17m)",
    korTitle: "동작 모방",
    description: "손뼉 치기, 만세, 뒷걸음질 동작을 차례로 보여주고 따라 하는지 관찰합니다.",
    variant: 'pink',
    instructionDuration: 15, // 각 지시사항당 15초
    instructions: [
      {
        id: 1,
        text: "아이와 눈을 맞추고",
        boldText: "가슴 높이에서",
        suffix: "정확하게 박수를 쳐주세요"
      },
      {
        id: 2,
        text: "아이를 바라보며",
        boldText: "양팔을 머리 위로",
        suffix: "쭉 뻗어 올려주세요 (만세)"
      },
      {
        id: 3,
        text: "아이를 바라보고 서서",
        boldText: "뒤로 3~4걸음",
        suffix: "천천히 물러나 주세요"
      },
    ],
    script: { lines: ["엄마(아빠) 따라 해볼까?", "짝짝짝! 만세!", "뒤로 엉금엉금~"] }
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
    instructionDuration: 15, // 각 지시사항당 15초
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
    engTitle: "Vocal Imitation (12-17m)",
    korTitle: "발화 모방 자극",
    description: "제시된 단어(아, 마, 바, 맘마, 까꿍)를 들려주고 아이가 따라 말하는지 관찰합니다.",
    variant: 'amber',
    instructionDuration: 5, // 각 지시사항당 5초
    instructions: [
      // 1. 아
      { id: 1, text: "[ 아 ] 소리를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 2, text: "[ 아 ] 소리를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 3, text: "[ 아 ] 소리를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },

      // 2. 마
      { id: 4, text: "[ 마 ] 소리를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 5, text: "[ 마 ] 소리를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 6, text: "[ 마 ] 소리를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },

      // 3. 바
      { id: 7, text: "[ 바 ] 소리를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 8, text: "[ 바 ] 소리를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 9, text: "[ 바 ] 소리를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },

      // 4. 맘마
      { id: 10, text: "[ 맘마 ] 단어를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 11, text: "[ 맘마 ] 단어를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 12, text: "[ 맘마 ] 단어를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },

      // 5. 까꿍
      { id: 13, text: "[ 까꿍 ] 단어를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 14, text: "[ 까꿍 ] 단어를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 15, text: "[ 까꿍 ] 단어를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },
    ],
    script: { lines: ["화면에 보이는 단어를", "정확하게 한 번만", "말해 주세요."] }
  },

  // =================================================================
  // TASK 2: 언어/발화 모방 (SPEECH_IMITATION)
  // [18-23개월] 자극: 엄마, 우유, 자동차, 까까 주세요, 야호
  // 총 15단계 (5개 단어 * 3회 반복)
  // =================================================================
  "SPEECH_IMITATION_18M": {
    step: "02",
    engTitle: "Vocal Imitation (18-23m)",
    korTitle: "발화 모방 자극",
    description: "제시된 단어(엄마, 우유, 자동차, 까까 주세요, 야호)를 들려주고 아이가 따라 말하는지 관찰합니다.",
    variant: 'amber',
    instructionDuration: 5, // 각 지시사항당 5초
    instructions: [
      // 1. 엄마
      { id: 1, text: "[ 엄마 ] 단어를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 2, text: "[ 엄마 ] 단어를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 3, text: "[ 엄마 ] 단어를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },

      // 2. 우유
      { id: 4, text: "[ 우유 ] 단어를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 5, text: "[ 우유 ] 단어를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 6, text: "[ 우유 ] 단어를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },

      // 3. 자동차
      { id: 7, text: "[ 자동차 ] 단어를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 8, text: "[ 자동차 ] 단어를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 9, text: "[ 자동차 ] 단어를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },

      // 4. 까까 주세요
      { id: 10, text: "[ 까까 주세요 ] 문장을", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 11, text: "[ 까까 주세요 ] 문장을", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 12, text: "[ 까까 주세요 ] 문장을 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },

      // 5. 야호
      { id: 13, text: "[ 야호! ] 감탄사를", boldText: "한 번만 말하고", suffix: "5초간 기다려주세요" },
      { id: 14, text: "[ 야호! ] 감탄사를", boldText: "한 번 더 말하고", suffix: "기다려주세요" },
      { id: 15, text: "[ 야호! ] 감탄사를 마지막으로", boldText: "한 번 더 말하고", suffix: "반응을 관찰해주세요" },
    ],
    script: { lines: ["화면에 보이는 단어를", "정확하게 한 번씩", "말해 주세요."] }
  },
  // =================================================================
  // TASK 3: 비대면 호명 반응 (NAME_NON_FACING)
  // 1-2(평소) -> 3-4(큰소리) -> 5-6(애칭)
  // =================================================================
  "NAME_NON_FACING": {
    step: "03",
    engTitle: "Name Response (Offline)",
    korTitle: "비대면 호명 반응",
    description: "아이의 시야 밖에서\n이름을 불렀을 때\n고개를 돌려 반응하는지\n확인합니다.\n\n아이는 카메라를 등지게 하고,\n보호자는 아이의 뒤에서\n카메라 방향으로 크게 두 발자국 이동하여\n검사를 시행해 주세요.\n\n보호자와 아이 모두\n화면에 나와야 하며,\n각 지시가 끝날 때마다\n보호자는 화면을 보고\n다음 가이드를 확인해 주시기 바랍니다.",
    variant: 'violet',
    countdown: 10,
    instructionDuration: 8, // 각 지시사항당 8초
    instructions: [
      { id: 1, text: "시야 밖(등 뒤)에서", boldText: "평소 목소리로", suffix: "이름을 불러주세요" },
      { id: 2, text: "한번 더", boldText: "평소 목소리로", suffix: "한 번 더 불러주세요" },
      { id: 3, text: "반응이 없다면", boldText: "크고 높은 톤으로", suffix: "이름을 불러주세요" },
      { id: 4, text: "여전히 반응이 없다면", boldText: "크고 높은 톤으로", suffix: "다시 불러주세요" },
      { id: 5, text: "반응이 없다면", boldText: "애칭을 섞어", suffix: "다정한 목소리로 불러보세요" },
      { id: 6, text: "마지막으로", boldText: "여기봐!를 붙여서 이름을 함께", suffix: "불러보세요" },
    ],
    script: { lines: ["아이의 이름을", "ㅇㅇ아! 라고 불러주세요"] }
  },

  // =================================================================
  // TASK 4: 대면 호명 반응 (NAME_FACING)
  // 1(시도) -> 2(재시도) -> 3(재시도)
  // =================================================================
  "NAME_FACING": {
    step: "04",
    engTitle: "Name Response (Visual)",
    korTitle: "대면 호명 반응",
    description: "마주 본 상태에서 이름을 불렀을 때 눈을 맞추는지 확인합니다.",
    variant: 'emerald',
    instructionDuration: 8, // 각 지시사항당 8초
    instructions: [
      { id: 1, text: "아이와 마주 본 상태에서", boldText: "이름을 부르고", suffix: "눈맞춤을 확인하세요" },
      { id: 2, text: "아이와 마주 본 상태에서", boldText: "이름을", suffix: "한 번 더 불러주세요" },
      { id: 3, text: "마지막으로", boldText: "이름을 부르고", suffix: "눈을 맞추는지 확인하세요" },
    ],
    script: { lines: ["아이의 이름을 부르고", "눈을 맞추는지", "잠깐 기다리며 확인해주세요"] }
  }
}
export const VIDEO_TYPE_MAP: Record<string, string> = {
  'POSE_IMITATION_12M': 'TASK1',
  'POSE_IMITATION_18M': 'TASK1',
  'SPEECH_IMITATION_12M': 'TASK2',
  'SPEECH_IMITATION_18M': 'TASK2',
  'NAME_NON_FACING': 'TASK3',
  'NAME_FACING': 'TASK4'
};

export const CLIENT_TO_SERVER_VIDEO_TYPE_MAP: Record<string, string> = {
  'TASK1': 'POSE_IMITATION',
  'TASK2': 'SPEECH_IMITATION',
  'TASK3': 'NAME_NON_FACING',
  'TASK4': 'NAME_FACING',
  '1': 'POSE_IMITATION',
  '2': 'SPEECH_IMITATION',
  '3': 'NAME_NON_FACING',
  '4': 'NAME_FACING',
  // Identity Mappings
  'POSE_IMITATION': 'POSE_IMITATION',
  'SPEECH_IMITATION': 'SPEECH_IMITATION',
  'NAME_NON_FACING': 'NAME_NON_FACING',
  'NAME_FACING': 'NAME_FACING',
  'POSE_IMITATION_12M': 'POSE_IMITATION',
  'POSE_IMITATION_18M': 'POSE_IMITATION',
  'SPEECH_IMITATION_12M': 'SPEECH_IMITATION',
  'SPEECH_IMITATION_18M': 'SPEECH_IMITATION'
};