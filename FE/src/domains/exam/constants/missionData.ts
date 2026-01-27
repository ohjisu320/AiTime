// src/domains/exam/constants/missionData.ts [cite: 2026-01-27]

export const SCREENING_CONTENT: Record<string, any> = {
  "1": { // TASK1: 동작 모방 (12-17개월 예시) [cite: 2026-01-27]
    step: "01",
    engTitle: "Action Imitation",
    korTitle: "동작 모방하기",
    instructions: [
      { id: 1, text: "아이와 눈을 맞춘 상태에서", boldText: "가슴 높이", suffix: "에서 준비해주세요" },
      { id: 2, text: "정확하게", boldText: "3번 이상", suffix: "박수를 쳐주세요" },
    ],
    script: { lines: ["자, 엄마(아빠) 봐봐!", "짝! 짝! 짝!", "우리 ㅇㅇ이도 해볼까?"] }
  },
  "2": { // TASK2: 언어/발화 모방 [cite: 2026-01-27]
    step: "02",
    engTitle: "Vocal Imitation",
    korTitle: "발화 모방 자극",
    instructions: [
      { id: 1, text: "화면에 보이는 자극을", boldText: "한 번만", suffix: "말해주세요" },
      { id: 2, text: "아이의 첫 발화까지", boldText: "3~5초간", suffix: "조용히 기다려주세요" },
    ],
    script: { lines: ["좋아요. 화면에 보이는", "자극(예: 맘마, 까꿍)을", "한 번만 말해 주세요."] }
  },
  "3": { // TASK3: 비대면 호명 반응 [cite: 2026-01-27]
    step: "03",
    engTitle: "Name Response (Offline)",
    korTitle: "비대면 호명 반응",
    instructions: [
      { id: 1, text: "아이의 등 뒤나", boldText: "시야 밖 사각지대", suffix: "로 이동해주세요" },
      { id: 2, text: "신체 접촉 없이", boldText: "이름만", suffix: "명확하게 불러주세요" },
    ],
    script: { lines: ["평소 목소리 톤으로", "아이의 이름을", "ㅇㅇ아! 라고 불러주세요"] }
  },
  "4": { // TASK4: 대면 호명 반응 [cite: 2026-01-27]
    step: "04",
    engTitle: "Name Response (Visual)",
    korTitle: "대면 호명 반응",
    instructions: [
      { id: 1, text: "아이와 부모님이", boldText: "화면 중앙", suffix: "에 들어오게 해주세요" },
      { id: 2, text: "아이가 부모님과", boldText: "마주보게", suffix: "한 뒤 이름을 불러주세요" },
    ],
    script: { lines: ["아이의 이름을 부르고", "눈을 맞추는지", "잠깐 기다리며 확인해주세요"] }
  }
};